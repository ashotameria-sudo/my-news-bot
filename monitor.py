import requests
from bs4 import BeautifulSoup
import os

# --- CONFIGURATION ---
URLS = [
    "https://mamul.am/news",  # Change these to your actual sites
]
DB_FILE = "seen_links.txt"

# Get secrets from GitHub Environment
TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    if not TOKEN or not CHAT_ID:
        return
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "HTML"}
    requests.post(url, data=payload)

def get_links(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Extracts all links. You might need to adjust this for specific sites.
        return {a['href'] for a in soup.find_all('a', href=True) if len(a['href']) > 20}
    except:
        return set()

def main():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            seen = set(line.strip() for line in f)
    else:
        seen = set()

    new_articles = []
    for url in URLS:
        links = get_links(url)
        for link in links:
            # Ensure the link is full (adds domain if it's a relative path)
            full_link = link if link.startswith('http') else f"{url.rstrip('/')}/{link.lstrip('/')}"
            if full_link not in seen:
                new_articles.append(full_link)
                seen.add(full_link)

    if new_articles:
        # Send to Telegram
        msg = "<b>New Articles Found:</b>\n\n" + "\n".join(new_articles[:10]) # Send first 10
        send_telegram(msg)
        
        # Save updated list
        with open(DB_FILE, 'w') as f:
            for item in seen:
                f.write(item + "\n")

if __name__ == "__main__":
    main()
