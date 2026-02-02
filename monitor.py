import requests
from bs4 import BeautifulSoup
import os

# --- CONFIGURATION ---
URLS = [
    
    "https://mamul.am/"
]
DB_FILE = "seen_links.txt"

def get_links(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # This finds all <a> tags with an href. 
        # You can refine this (e.g., soup.find_all('h3')) to be more specific.
        links = {a['href'] for a in soup.find_all('a', href=True) if len(a['href']) > 10}
        return links
    except Exception as e:
        print(f"Error checking {url}: {e}")
        return set()

def main():
    # Load previously seen links
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            seen = set(line.strip() for line in f)
    else:
        seen = set()

    new_links = []
    current_all_links = set()

    for url in URLS:
        found_links = get_links(url)
        for link in found_links:
            # Simple filter: check if it's a new link
            if link not in seen:
                new_links.append(link)
            current_all_links.add(link)

    # Report findings
    if new_links:
        print(f"Found {len(new_links)} new articles:")
        for l in new_links:
            print(l)
        
        # Update the text file with new links
        with open(DB_FILE, 'a') as f:
            for l in new_links:
                f.write(l + "\n")
    else:
        print("No new articles found.")

if __name__ == "__main__":
    main()
