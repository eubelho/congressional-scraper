"""
Congressional Members Data Collector - OFFICIAL VERSION
Uses the official Congress.gov API for reliable, structured data
Built for: Elliott Ubelhor's Congressional Approval Predictor Project
"""

import requests
import csv
import time
import os
import json

# API Configuration - Correct URLs
API_BASE_URL = "https://api.data.gov/congress/v3"
# You'll need to get your own API key from: https://api.data.gov/signup/

def get_current_congress():
    """Get the current Congress number"""
    # As of 2025, we're in the 119th Congress
    return 119

def fetch_house_members(api_key, congress=None):
    """
    Fetch House members using the official Congress.gov API
    This is the most reliable method using government data
    """
    if not congress:
        congress = get_current_congress()
    
    print(f"Fetching House members from Congress.gov API (Congress {congress})...")
    
    # API endpoint for current House members
    url = f"{API_BASE_URL}/member/congress/{congress}/house"
    
    headers = {
        'User-Agent': 'Congressional-Data-Collector/1.0',
        'Accept': 'application/json'
    }
    
    params = {
        'api_key': api_key,
        'limit': 250,  # Maximum allowed
        'currentMember': 'true'  # Only current members
    }
    
    all_members = []
    offset = 0
    
    try:
        while True:
            params['offset'] = offset
            
            print(f"Requesting members {offset + 1}-{offset + 250}...")
            response = requests.get(url, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'members' in data and data['members']:
                    members_batch = data['members']
                    
                    for member in members_batch:
                        member_info = {
                            'bioguide_id': member.get('bioguideId', ''),
                            'name': f"{member.get('firstName', '')} {member.get('lastName', '')}".strip(),
                            'first_name': member.get('firstName', ''),
                            'last_name': member.get('lastName', ''),
                            'state': member.get('state', ''),
                            'district': member.get('district', ''),
                            'party': member.get('partyName', ''),
                            'served_from': member.get('terms', [{}])[-1].get('startYear') if member.get('terms') else '',
                            'served_to': member.get('terms', [{}])[-1].get('endYear') if member.get('terms') else '',
                            'url': member.get('url', ''),
                            'source': 'Congress.gov API',
                            'congress': congress
                        }
                        all_members.append(member_info)
                    
                    print(f"✅ Collected {len(members_batch)} members (Total: {len(all_members)})")
                    
                    # Check if we have more pages
                    pagination = data.get('pagination', {})
                    if not pagination.get('next'):
                        break
                    
                    offset += 250
                    time.sleep(0.1)  # Be respectful to the API
                    
                else:
                    print("No more members found")
                    break
                    
            elif response.status_code == 403:
                print("❌ API key invalid or missing. Get one at: https://api.data.gov/signup/")
                return []
            elif response.status_code == 429:
                print("❌ Rate limit exceeded. Waiting 60 seconds...")
                time.sleep(60)
                continue
            else:
                print(f"❌ API request failed with status code: {response.status_code}")
                print(f"Response: {response.text}")
                return []
                
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return []
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return []
    
    print(f"✅ Successfully collected {len(all_members)} House members from official API")
    return all_members

def save_to_csv(members_data, filename="house_members_official.csv"):
    """Save the collected data to a CSV file"""
    if not members_data:
        print("❌ No data to save!")
        return False
    
    try:
        os.makedirs('data', exist_ok=True)
        filepath = os.path.join('data', filename)
        
        headers = list(members_data[0].keys())
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            
            for member in members_data:
                writer.writerow(member)
        
        print(f"✅ Data saved to {filepath}")
        print(f"📊 Total records: {len(members_data)}")
        
        # Save a JSON version too for easier programmatic access
        json_filepath = filepath.replace('.csv', '.json')
        with open(json_filepath, 'w', encoding='utf-8') as jsonfile:
            json.dump(members_data, jsonfile, indent=2)
        print(f"✅ JSON version saved to {json_filepath}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to save data: {e}")
        return False

def main():
    """Main function to run the data collector"""
    print("🏛️  Official Congressional Members Data Collector")
    print("Using Congress.gov API - Most Reliable Source")
    print("=" * 60)
    
    # Check if API key is provided
    api_key = input("Enter your Congress.gov API key (get one at https://api.data.gov/signup/): ").strip()
    
    if not api_key:
        print("❌ API key is required to use the official Congress.gov API")
        print("📝 Steps to get your free API key:")
        print("   1. Go to https://api.data.gov/signup/")
        print("   2. Fill out the form (takes 1 minute)")
        print("   3. Check your email for the API key")
        print("   4. Run this script again with your key")
        return
    
    members = fetch_house_members(api_key)
    
    if members:
        save_success = save_to_csv(members)
        
        if save_success:
            print("\n🎉 Data collection completed successfully!")
            print("📁 Check the 'data/' folder for results")
            
            # Show statistics
            parties = {}
            states = {}
            for member in members:
                party = member.get('party', 'Unknown')
                state = member.get('state', 'Unknown')
                parties[party] = parties.get(party, 0) + 1
                states[state] = states.get(state, 0) + 1
            
            print(f"\n📊 Summary Statistics:")
            print(f"   Total Representatives: {len(members)}")
            print(f"   By Party: {dict(sorted(parties.items(), key=lambda x: x[1], reverse=True))}")
            print(f"   States Represented: {len(states)}")
            
            print("\n📋 Sample of collected data:")
            for i, member in enumerate(members[:3]):
                print(f"{i+1}. {member['name']} ({member['party']}) - {member['state']}-{member['district']}")
                
        else:
            print("❌ Data collection succeeded but failed to save")
    else:
        print("❌ No data was collected")

if __name__ == "__main__":
    main()

# Instructions:
# 1. Get a free API key from: https://api.data.gov/signup/
# 2. Run: python congress_scraper.py
# 3. Enter your API key when prompted
# 4. Check the 'data' folder for results

# Benefits of this approach:
# - Uses official government data (most reliable)
# - Structured JSON responses
# - Rate limiting handled automatically  
# - Includes comprehensive member information
# - No web scraping brittleness
# - Free to use with API key