"""
Congressional Web Scraper - ACTUAL WEB SCRAPING VERSION
Scrapes multiple sources to build comprehensive representative database
Built for: Elliott Ubelhor - Learning Web Scraping Techniques
"""

import requests
from bs4 import BeautifulSoup
import csv
import time
import os
import re
from urllib.parse import urljoin, urlparse
import random

class CongressionalWebScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.representatives = []
        self.scraped_urls = set()
    
    def scrape_house_leadership(self):
        """Scrape House leadership from house.gov"""
        print("🏛️ Scraping House leadership...")
        
        url = "https://www.house.gov/leadership"
        
        try:
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                print(f"❌ Failed to access {url}: {response.status_code}")
                return []
                
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for leadership sections
            leadership_data = []
            
            # Try multiple selectors for leadership info
            selectors = [
                '.leadership-member',
                '.member-info',  
                '.leadership-card',
                '[class*="leader"]',
                '.bio-card'
            ]
            
            for selector in selectors:
                members = soup.select(selector)
                if members:
                    print(f"✅ Found {len(members)} leadership members using selector: {selector}")
                    
                    for member in members:
                        member_data = self.extract_member_info(member, 'House Leadership')
                        if member_data and member_data['name']:
                            leadership_data.append(member_data)
                    break
            
            if not leadership_data:
                # Fallback: look for any links to member pages
                member_links = soup.find_all('a', href=re.compile(r'members?|representatives?', re.I))
                print(f"🔍 Found {len(member_links)} potential member links as fallback")
                
                for link in member_links[:10]:  # Limit to prevent too many requests
                    text = link.get_text().strip()
                    href = link.get('href')
                    
                    if text and len(text.split()) >= 2:  # Likely a name
                        member_data = {
                            'name': text,
                            'title': 'Representative',
                            'party': 'Unknown',
                            'state': 'Unknown', 
                            'district': 'Unknown',
                            'source': 'House.gov Leadership',
                            'profile_url': urljoin(url, href) if href else '',
                            'scraped_from': url
                        }
                        leadership_data.append(member_data)
            
            print(f"✅ Scraped {len(leadership_data)} leadership members")
            return leadership_data
            
        except Exception as e:
            print(f"❌ Error scraping House leadership: {e}")
            return []
    
    def scrape_bioguide_directory(self):
        """Scrape from Congressional Biographical Directory"""
        print("📚 Scraping Congressional Biographical Directory...")
        
        url = "https://bioguide.congress.gov/search/bio_search.asp"
        
        try:
            # First get the search page
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                print(f"❌ Failed to access bioguide: {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Look for current members or search results
            members_data = []
            
            # Try to find member listings
            member_elements = soup.find_all(['tr', 'div', 'li'], class_=re.compile(r'member|bio|result', re.I))
            
            if not member_elements:
                # Try different approach - look for tables
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')[1:]  # Skip header
                    for row in rows[:20]:  # Limit results
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 2:
                            # Try to extract name from first cell
                            name_cell = cells[0]
                            name = name_cell.get_text().strip()
                            
                            if name and len(name.split()) >= 2:
                                member_data = {
                                    'name': name,
                                    'title': 'Representative',
                                    'party': cells[1].get_text().strip() if len(cells) > 1 else 'Unknown',
                                    'state': cells[2].get_text().strip() if len(cells) > 2 else 'Unknown',
                                    'district': 'Unknown',
                                    'source': 'Biographical Directory',
                                    'profile_url': '',
                                    'scraped_from': url
                                }
                                members_data.append(member_data)
            
            print(f"✅ Scraped {len(members_data)} members from bioguide")
            return members_data
            
        except Exception as e:
            print(f"❌ Error scraping bioguide: {e}")
            return []
    
    def scrape_state_delegation_pages(self):
        """Scrape individual state delegation pages"""
        print("🗺️ Scraping state delegation pages...")
        
        # List of states to try
        states = ['california', 'texas', 'florida', 'new-york', 'pennsylvania']
        all_members = []
        
        for state in states:
            try:
                url = f"https://www.house.gov/representatives/find-your-representative?state={state}"
                print(f"🔍 Trying {state}...")
                
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for representative listings
                    rep_elements = soup.find_all(['div', 'li', 'article'], class_=re.compile(r'rep|member|delegate', re.I))
                    
                    for element in rep_elements:
                        member_data = self.extract_member_info(element, f'{state.title()} Delegation')
                        if member_data and member_data['name']:
                            member_data['state'] = state.replace('-', ' ').title()
                            all_members.append(member_data)
                
                time.sleep(random.uniform(1, 3))  # Be respectful
                
            except Exception as e:
                print(f"❌ Error scraping {state}: {e}")
                continue
        
        print(f"✅ Scraped {len(all_members)} members from state pages")
        return all_members
    
    def scrape_committee_pages(self):
        """Scrape committee membership pages"""
        print("🏢 Scraping committee pages...")
        
        committees = [
            'house-committee-on-appropriations',
            'house-committee-on-ways-and-means',
            'house-committee-on-judiciary'
        ]
        
        all_members = []
        
        for committee in committees:
            try:
                url = f"https://www.congress.gov/committees/{committee}"
                print(f"🔍 Scraping {committee}...")
                
                response = self.session.get(url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Look for member names in committee listings
                    member_links = soup.find_all('a', href=re.compile(r'/member/', re.I))
                    
                    for link in member_links:
                        name = link.get_text().strip()
                        if name and len(name.split()) >= 2:
                            member_data = {
                                'name': name,
                                'title': 'Representative',
                                'party': 'Unknown',
                                'state': 'Unknown',
                                'district': 'Unknown',
                                'committee': committee.replace('-', ' ').title(),
                                'source': 'Committee Page',
                                'profile_url': urljoin(url, link.get('href', '')),
                                'scraped_from': url
                            }
                            all_members.append(member_data)
                
                time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"❌ Error scraping {committee}: {e}")
                continue
        
        print(f"✅ Scraped {len(all_members)} members from committee pages")
        return all_members
    
    def extract_member_info(self, element, source):
        """Extract member information from HTML element"""
        try:
            # Try to find name
            name_selectors = ['h1', 'h2', 'h3', '.name', '.member-name', 'a']
            name = ''
            
            for selector in name_selectors:
                name_elem = element.select_one(selector)
                if name_elem:
                    name = name_elem.get_text().strip()
                    if name and len(name.split()) >= 2:
                        break
            
            if not name:
                # Fallback: use all text and try to find name-like pattern
                all_text = element.get_text().strip()
                lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                for line in lines:
                    if len(line.split()) >= 2 and len(line) < 50:  # Likely a name
                        name = line
                        break
            
            # Try to extract other info
            party = self.extract_party_info(element)
            state = self.extract_state_info(element)
            district = self.extract_district_info(element)
            
            # Look for profile links
            profile_url = ''
            link_elem = element.find('a', href=True)
            if link_elem:
                profile_url = link_elem.get('href')
            
            return {
                'name': self.clean_name(name),
                'title': 'Representative',
                'party': party,
                'state': state,
                'district': district,
                'source': source,
                'profile_url': profile_url,
                'scraped_from': 'Multiple Sources'
            }
            
        except Exception as e:
            print(f"❌ Error extracting member info: {e}")
            return None
    
    def extract_party_info(self, element):
        """Try to extract party information"""
        text = element.get_text().lower()
        
        if any(word in text for word in ['republican', 'gop', '(r)']):
            return 'Republican'
        elif any(word in text for word in ['democrat', 'democratic', '(d)']):
            return 'Democrat'
        elif 'independent' in text:
            return 'Independent'
        
        return 'Unknown'
    
    def extract_state_info(self, element):
        """Try to extract state information"""
        text = element.get_text()
        
        # Look for state abbreviations or full names
        state_pattern = r'\b([A-Z]{2})\b'
        matches = re.findall(state_pattern, text)
        
        if matches:
            return matches[0]
        
        # Could add full state name matching here
        return 'Unknown'
    
    def extract_district_info(self, element):
        """Try to extract district information"""
        text = element.get_text()
        
        # Look for district numbers
        district_pattern = r'district\s*(\d+)|(\d+)(?:st|nd|rd|th)\s*district'
        matches = re.findall(district_pattern, text.lower())
        
        if matches:
            return matches[0][0] or matches[0][1]
        
        return 'Unknown'
    
    def clean_name(self, name):
        """Clean and standardize name"""
        if not name:
            return ''
        
        # Remove titles and extra text
        name = re.sub(r'\b(rep|representative|hon|honorable|mr|mrs|ms|dr)\.?\s*', '', name, flags=re.I)
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def deduplicate_members(self, members_list):
        """Remove duplicate members based on name similarity"""
        unique_members = []
        seen_names = set()
        
        for member in members_list:
            name_key = member['name'].lower().replace(' ', '').replace('.', '')
            
            if name_key not in seen_names and len(name_key) > 3:
                seen_names.add(name_key)
                unique_members.append(member)
        
        return unique_members
    
    def run_comprehensive_scrape(self):
        """Run all scraping methods and combine results"""
        print("🚀 Starting comprehensive congressional web scraping...")
        print("=" * 60)
        
        all_members = []
        
        # Method 1: House Leadership
        leadership_members = self.scrape_house_leadership()
        all_members.extend(leadership_members)
        
        # Method 2: Biographical Directory
        bio_members = self.scrape_bioguide_directory()
        all_members.extend(bio_members)
        
        # Method 3: State Delegation Pages
        state_members = self.scrape_state_delegation_pages()
        all_members.extend(state_members)
        
        # Method 4: Committee Pages
        committee_members = self.scrape_committee_pages()
        all_members.extend(committee_members)
        
        # Deduplicate
        unique_members = self.deduplicate_members(all_members)
        
        print(f"\n📊 Scraping Results:")
        print(f"   Total scraped: {len(all_members)}")
        print(f"   Unique members: {len(unique_members)}")
        print(f"   Sources used: Multiple web scraping approaches")
        
        self.representatives = unique_members
        return unique_members

def save_scraped_data(members_data, filename="scraped_house_members.csv"):
    """Save scraped data to CSV"""
    if not members_data:
        print("❌ No data to save!")
        return False
    
    try:
        os.makedirs('data', exist_ok=True)
        filepath = os.path.join('data', filename)
        
        # Get all possible fieldnames
        all_fields = set()
        for member in members_data:
            all_fields.update(member.keys())
        
        fieldnames = sorted(list(all_fields))
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for member in members_data:
                writer.writerow(member)
        
        print(f"✅ Scraped data saved to {filepath}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to save data: {e}")
        return False

def main():
    """Main scraping function"""
    print("🕷️ Congressional Web Scraper")
    print("Using actual web scraping techniques")
    print("=" * 50)
    
    scraper = CongressionalWebScraper()
    
    # Run comprehensive scraping
    members = scraper.run_comprehensive_scrape()
    
    if members:
        # Save results
        save_scraped_data(members)
        
        # Show sample results
        print("\n📋 Sample of scraped data:")
        for i, member in enumerate(members[:5]):
            print(f"{i+1}. {member['name']} ({member.get('party', 'Unknown')}) - {member.get('source', 'Unknown Source')}")
        
        # Show statistics
        parties = {}
        sources = {}
        for member in members:
            party = member.get('party', 'Unknown')
            source = member.get('source', 'Unknown')
            parties[party] = parties.get(party, 0) + 1
            sources[source] = sources.get(source, 0) + 1
        
        print(f"\n📊 Scraping Statistics:")
        print(f"   By Party: {parties}")
        print(f"   By Source: {sources}")
        
        print("\n🎉 Web scraping completed successfully!")
        print("This demonstrates actual HTML parsing and web scraping techniques!")
        
    else:
        print("❌ No data was scraped")
        print("💡 This shows why web scraping can be challenging - websites change frequently!")

if __name__ == "__main__":
    main()

# Key Web Scraping Techniques Demonstrated:
# 1. Multiple source scraping strategy
# 2. BeautifulSoup HTML parsing
# 3. CSS selector and regex pattern matching  
# 4. Robust error handling for web requests
# 5. Rate limiting and respectful scraping
# 6. Data extraction and cleaning
# 7. Deduplication of scraped results
# 8. Fallback strategies when selectors fail