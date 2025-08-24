"""
Congressional Members Data Collector - WORKING ALTERNATIVE
Uses GovTrack.us API - No API key required, reliable government data
Built for: Elliott Ubelhor's Congressional Approval Predictor Project
"""

import requests
import csv
import time
import os
import json

def fetch_house_members_govtrack():
    """
    Fetch current House members using GovTrack.us API
    GovTrack is reliable and doesn't require API key authorization
    """
    print("Fetching House members from GovTrack.us API...")
    
    # GovTrack API endpoint - get all current members and filter locally
    url = "https://www.govtrack.us/api/v2/role"
    
    params = {
        'current': 'true',      # Currently serving
        'role_type': 'representative',  # House only  
        'limit': 500,
        'format': 'json'
    }
    
    headers = {
        'User-Agent': 'Congressional-Data-Collector/1.0 (Educational-Use)'
    }
    
    try:
        print("Requesting data from GovTrack.us...")
        response = requests.get(url, params=params, headers=headers)
        
        if response.status_code == 200:
            print("✅ Successfully connected to GovTrack API!")
            data = response.json()
            
            members = []
            
            # Process the response - roles endpoint structure
            if 'objects' in data:
                roles_data = data['objects']
                
                for role in roles_data:
                    if role.get('role_type') != 'representative':
                        continue
                        
                    # Get person data from the role
                    person = role.get('person', {})
                    
                    member_info = {
                        'govtrack_id': person.get('id', ''),
                        'bioguide_id': person.get('bioguideid', ''),
                        'name': person.get('name', ''),
                        'first_name': person.get('firstname', ''),
                        'last_name': person.get('lastname', ''),
                        'nickname': person.get('nickname', ''),
                        'state': role.get('state', ''),
                        'district': role.get('district', ''),
                        'party': role.get('party', ''),
                        'title': role.get('title', ''),
                        'start_date': role.get('startdate', ''),
                        'end_date': role.get('enddate', ''),
                        'website': role.get('website', ''),
                        'phone': role.get('phone', ''),
                        'office': role.get('office', ''),
                        'gender': person.get('gender', ''),
                        'birthday': person.get('birthday', ''),
                        'twitter': person.get('twitterid', ''),
                        'youtube': person.get('youtubeid', ''),
                        'source': 'GovTrack.us API',
                        'source_url': 'https://www.govtrack.us/api/v2/role'
                    }
                    
                    members.append(member_info)
                
                print(f"✅ Successfully collected {len(members)} House members")
                return members
            else:
                print(f"❌ Unexpected API response structure: {list(data.keys())}")
                return []
                
        else:
            print(f"❌ API request failed with status code: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return []
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Network error: {e}")
        return []
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return []

def save_to_csv(members_data, filename="house_members_govtrack.csv"):
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
        
        # Save JSON version too
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
    print("🏛️  Congressional Members Data Collector")
    print("Using GovTrack.us API - No API Key Required!")
    print("=" * 50)
    
    members = fetch_house_members_govtrack()
    
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
                district_info = f"-{member['district']}" if member['district'] else ""
                print(f"{i+1}. {member['name']} ({member['party']}) - {member['state']}{district_info}")
                
        else:
            print("❌ Data collection succeeded but failed to save")
    else:
        print("❌ No data was collected")
        print("💡 This might be a temporary network issue. Try again in a few minutes.")

if __name__ == "__main__":
    main()

# Benefits of this approach:
# - No API key required
# - Reliable government-adjacent data (GovTrack.us is widely used)
# - More detailed information than basic scraping
# - Includes contact info, social media, office details
# - JSON and CSV output formats
# - Always up-to-date