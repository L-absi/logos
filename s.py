import requests
from bs4 import BeautifulSoup
import json
import time
import os

# جلب الرابط من Secrets
FIREBASE_URL = os.getenv('FIREBASE_URL')

def get_match_details(match_url):
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        res = requests.get(match_url, headers=headers, timeout=10)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        page_text = soup.get_text()
        commentator = "غير مدرج"
        channel = "غير مدرجة"
        
        # استخراج المعلق والقناة
        if "معلق:" in page_text:
            commentator = page_text.split("معلق:")[1].split("\n")[0].split("<")[0].strip()
        if "القنوات الناقلة:" in page_text:
            channel = page_text.split("القنوات الناقلة:")[1].split("\n")[0].split("<")[0].strip()
            
        return commentator, channel
    except:
        return "غير مدرج", "غير مدرجة"

def push_to_firebase(match_date, match_data):
    # تنظيف الـ ID من الرموز الممنوعة في Firebase لضمان عدم فشل الرفع
    forbidden_chars = [".", "$", "#", "[", "]", " "]
    match_id = f"{match_data['home_team']}_{match_data['away_team']}"
    for char in forbidden_chars:
        match_id = match_id.replace(char, "_")
    
    url = f"{FIREBASE_URL}/{match_date}/{match_id}.json"
    
    try:
        response = requests.put(url, json=match_data)
        if response.status_code == 200:
            print(f"✅ Synced: {match_data['home_team']} vs {match_data['away_team']}")
        else:
            print(f"⚠️ Failed: {response.status_code}")
    except Exception as e:
        print(f"❌ Firebase Error: {e}")

def run_scraper():
    if not FIREBASE_URL:
        print("❌ Error: FIREBASE_URL secret is not set in GitHub Settings!")
        return

    url = "https://www.kooora.com/?region=-1&area=0"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

    try:
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')

        scripts = soup.find_all('script', type='application/ld+json')
        count = 0
        
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') == 'SportsEvent':
                    match_url = data.get('url')
                    if not match_url.startswith("http"):
                        match_url = "https://www.kooora.com/" + match_url
                        
                    home_team = data.get('homeTeam', {}).get('name')
                    away_team = data.get('awayTeam', {}).get('name')
                    
                    commentator, channel = get_match_details(match_url)
                    match_date = data.get('startDate').split('T')[0]
                    
                    match_info = {
                        "league": data.get('description', '').split(' - ')[0],
                        "home_team": home_team,
                        "home_logo": data.get('homeTeam', {}).get('logo'),
                        "away_team": away_team,
                        "away_logo": data.get('awayTeam', {}).get('logo'),
                        "time": data.get('startDate'),
                        "commentator": commentator,
                        "channel": channel
                    }
                    
                    push_to_firebase(match_date, match_info)
                    count += 1
                    time.sleep(1.5) # زيادة التأخير قليلاً لضمان عدم الحظر في GitHub
            except:
                continue
        print(f"🏁 Total processed: {count}")
    except Exception as e:
        print(f"❌ Main Error: {e}")

if __name__ == "__main__":
    run_scraper()
