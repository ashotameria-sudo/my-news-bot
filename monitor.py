import requests
from bs4 import BeautifulSoup
import os
import json
import time
from datetime import datetime
import pytz

# --- CONFIGURATION ---
# Use the category pages for better coverage than the homepage
URLS = [
    "https://mamul.am/am/news"
]
DB_FILE = "seen_links.txt"
TIMEZONE = pytz.timezone('Asia/Yerevan')

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def get_today_articles(url):
    today_str = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
    new_found = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # FIND ALL NEWS LINKS: Search for any link containing /news/ and a number
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if "/news/" in href and any(char.isdigit() for char in href):
                full_link = href if href.startswith('http') else f"https://mamul.am{href}"
                links.append(full_link)
        
        # Remove duplicates from the list
        links = list(set(links))
        print(f"Checking {len(links)} potential links from {url}...")

        for full_link in links:
            # Skip checking if already in history to save time/resources
            # (History is loaded in main, but we check here too)
            
            time.sleep(1) # Be gentle to avoid blocks
            try:
                art_res = requests.get(full_link, headers=headers, timeout=10)
                art_soup = BeautifulSoup(art_res.text, 'html.parser')
                
                # Check for "datePublished" in the JSON-LD
                is_today = False
                scripts = art_soup.find_all('script', type='application/ld+json')
                for script in scripts:
                    if today_str in (script.string or ''):
                        is_today = True
                        break
                
                # FALLBACK: Check meta tags if JSON is missing
                if not is_today:
                    meta = art_soup.find("meta", property="article:published_time")
                    if meta and today_str in meta.get('content', ''):
                        is_today = True

                if is_today:
                    new_found.append(full_link)
            except:
                continue
                
        return set(new_found)
    except Exception as e:
        print(f"Error: {e}")
        return set()

def main():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            seen = set(line.strip() for line in f)
    else:
        seen = set()

    found_today = []
    for url in URLS:
        links = get_today_articles(url)
        for link in links:
            if link not in seen:
                found_today.append(link)
                seen.add(link)

    if found_today:
        msg = f"<b>📰 New Articles ({datetime.now(TIMEZONE).strftime('%H:%M')}):</b>\n\n"
        msg += "\n\n".join(found_today[:10]) # Send in batches of 10
        
        # Send to Telegram
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "HTML"})
        
        # Update history
        with open(DB_FILE, 'w') as f:
            for item in seen:
                f.write(item + "\n")

if __name__ == "__main__":
    main()
