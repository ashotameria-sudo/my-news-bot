import requests
from bs4 import BeautifulSoup
import os
from datetime import datetime

# --- CONFIGURATION ---
URLS = [
    "https://mamul.am/am/news/", 
]
DB_FILE = "seen_links.txt"

# Telegram Config
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    if not TOKEN or not CHAT_ID: return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=payload)

def is_published_today(article_element):
    """
    Checks if the article has today's date. 
    Note: You may need to adjust the tag names ('time' or 'span') 
    based on your specific news site's HTML.
    """
    today_str = datetime.now().strftime("%Y-%m-%d") # e.g., 2026-02-02
    
    # Common news site patterns:
    # 1. Look for <time datetime="2026-02-02">
    time_tag = article_element.find('time')
    if time_tag and time_tag.get('datetime'):
        return today_str in time_tag.get('datetime')
    
    # 2. Look for text like "Feb 2, 2026" inside the element
    today_human = datetime.now().strftime("%b %-d") # e.g., Feb 2
    if today_human in article_element.get_text():
        return True
        
    return False

def get_today_articles(url):
    new_found = []
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Most news sites wrap articles in <article> or <div class="post">
        # Adjust 'article' to match your site's structure
        articles = soup.find_all(['article', 'div'], class_=True) 
        
        for item in articles:
            link_tag = item.find('a', href=True)
            if link_tag and is_published_today(item):
                link = link_tag['href']
                full_link = link if link.startswith('http') else f"{url.rstrip('/')}/{link.lstrip('/')}"
                new_found.append(full_link)
                
        return set(new_found)
    except Exception as e:
        print(f"Error: {e}")
        return set()

def main():
    # Load history
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            seen = set(line.strip() for line in f)
    else:
        seen = set()

    today_links = []
    for url in URLS:
        links = get_today_articles(url)
        for l in links:
            if l not in seen:
                today_links.append(l)
                seen.add(l)

    if today_links:
        msg = f"<b>Today's New Articles ({datetime.now().strftime('%d %b')}):</b>\n\n"
        msg += "\n".join(today_links[:10])
        send_telegram(msg)
        
        with open(DB_FILE, 'w') as f:
            for item in seen: f.write(item + "\n")

if __name__ == "__main__":
    main()
