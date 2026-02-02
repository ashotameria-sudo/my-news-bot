import requests
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime
import pytz # You may need to add: pip install pytz

# --- CONFIGURATION ---
URLS = ["https://mamul.am/am/news"]
DB_FILE = "seen_links.txt"
TIMEZONE = pytz.timezone('Asia/Yerevan') # Set to the news site's timezone

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_today_articles(url):
    # Get "Today" based on the site's local time
    today_str = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
    new_found = []
    
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all potential news links
        links = {a['href'] for a in soup.find_all('a', href=True) if "/news/" in a['href']}
        
        for href in links:
            full_link = href if href.startswith('http') else f"https://mamul.am{href}"
            
            # Skip if it's clearly a category link, not an article
            if len(full_link.split('/')) < 6: continue 

            # Visit article to check JSON-LD
            art_res = requests.get(full_link, headers=headers, timeout=5)
            art_soup = BeautifulSoup(art_res.text, 'html.parser')
            scripts = art_soup.find_all('script', type='application/ld+json')
            
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    pub_date = data.get('datePublished', '')
                    # DEBUG: See what the script is finding in your GitHub Logs
                    print(f"Checking {full_link}: Found Date {pub_date}")
                    
                    if pub_date.startswith(today_str):
                        new_found.append(full_link)
                        break
                except:
                    continue
        return set(new_found)
    except Exception as e:
        print(f"Error: {e}")
        return set()
