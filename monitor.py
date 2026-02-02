import time # Add this at the top

def get_today_articles(url):
    today_str = datetime.now(TIMEZONE).strftime("%Y-%m-%d")
    new_found = []
    
    # Use a more complete header to look like a real browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://google.com'
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Look specifically for article links in the news list
        links = {a['href'] for a in soup.find_all('a', href=True) if "/news/" in a['href']}
        
        for href in links:
            full_link = href if href.startswith('http') else f"https://mamul.am{href}"
            
            # 1. Be polite: wait 2 seconds between articles to avoid blocks
            time.sleep(2) 
            
            try:
                art_res = requests.get(full_link, headers=headers, timeout=10)
                art_soup = BeautifulSoup(art_res.text, 'html.parser')
                
                # Check JSON-LD but also check meta tags as a backup
                is_today = False
                scripts = art_soup.find_all('script', type='application/ld+json')
                
                for script in scripts:
                    if today_str in (script.string or ''):
                        is_today = True
                        break
                
                # Backup: Check for meta tags if JSON-LD fails
                if not is_today:
                    meta_date = art_soup.find("meta", property="article:published_time")
                    if meta_date and today_str in meta_date.get('content', ''):
                        is_today = True

                if is_today:
                    print(f"✅ Found today: {full_link}")
                    new_found.append(full_link)
                else:
                    print(f"❌ Wrong date or old: {full_link}")

            except Exception as e:
                print(f"⚠️ Failed to read article {full_link}: {e}")
                
        return set(new_found)
    except Exception as e:
        print(f"Critical error: {e}")
        return set()
