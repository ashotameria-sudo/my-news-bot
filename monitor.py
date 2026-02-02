import requests
from bs4 import BeautifulSoup
import os
import json
from datetime import datetime

# --- CONFIGURATION ---
URLS = [
    "https://mamul.am/am/news",  # You can add more URLs here
]
DB_FILE = "seen_links.txt"

# Telegram Secrets from GitHub
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    if not TOKEN or not CHAT_ID:
        print("Telegram secrets not set.")
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML", "disable_web_page_preview": False}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Error sending to Telegram: {e}")

def get_today_articles(url):
    today_str = datetime.now().strftime("%Y-%m-%d") # e.g. 2026-02-02
    new_links = []
    
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Find all news items on the page (usually in <div> or <li>)
        # We look for all links first
        all_links = soup.find_all('a', href=True)
        
        for a in all_links:
            href = a['href']
            # Only process actual news links (specific to mamul.am structure)
            if "/news/" in href:
                full_link = href if href.startswith('http') else f"https://mamul.am{href}"
                
                # 2. Visit the article page to check the HIDDEN date Published
                # This ensures 100% accuracy based on the code you found
                art_res = requests.get(full_link, headers=headers, timeout=5)
                art_soup = BeautifulSoup(art_res.text, 'html.parser')
                
                scripts = art_soup.find_all('script', type='application/ld+json')
                is_today = False
                
                for script in scripts:
                    try:
                        data = json.loads(script.string)
                        # Check for the code you found: "datePublished": "2026-02-02..."
                        pub_date = data.get('datePublished', '')
                        if pub_date.startswith(today_str):
                            is_today = True
                            break
                    except:
                        continue
                
                if is_today:
                    new_links.append(full_link)

        return set(new_links)
    except Exception as e:
        print(f"Error scanning {url}: {e}")
        return set()

def main():
    # Load history to avoid duplicates
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
        # Send to Telegram (Limit to 10 to avoid spam)
        msg = f"<b>📰 New Articles Today ({datetime.now().strftime('%Y-%m-%d')}):</b>\n\n"
        msg += "\n\n".join(found_today[:10])
        send_telegram(msg)
        
        # Save history
        with open(DB_FILE, 'w') as f:
            for item in seen:
                f.write(item + "\n")
    else:
        print("No new articles found for today.")

if __name__ == "__main__":
    main()
