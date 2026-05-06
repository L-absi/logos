import requests
from bs4 import BeautifulSoup
import json
import time
import os
from datetime import datetime

# جلب الرابط من Secrets
FIREBASE_URL = os.getenv('FIREBASE_URL')

def get_match_details(match_url):
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept-Language": "ar,en;q=0.9"
        }
        res = requests.get(match_url, headers=headers, timeout=15)
        res.encoding = 'utf-8'
        soup = BeautifulSoup(res.text, 'html.parser')
        
        commentator = "غير مدرج"
        channel = "غير مدرجة"
        
        # البحث عن المعلق
        comm_text = soup.find(text=lambda t: "معلق:" in t)
        if comm_text:
            commentator = comm_text.split("معلق:")[1].strip()

        # البحث عن القنوات الناقلة (الأيقونات والنصوص)
        tv_icons = soup.find_all(['span', 'img'], {'class': 'tv_icon'})
        if tv_icons:
            channels_list = [icon.get('title') or icon.get('alt') for icon in tv_icons if icon.get('title') or icon.get('alt')]
            if channels_list:
                channel = " | ".join(list(set(channels_list)))
        
        if channel == "غير مدرجة":
            chan_text = soup.find(text=lambda t: "القنوات الناقلة:" in t)
            if chan_text:
                channel = chan_text.split("القنوات الناقلة:")[1].strip()

        return commentator, channel
    except:
        return "غير مدرج", "غير مدرجة"

def push_to_firebase(match_date, league_name, match_data):
    # تنظيف الأسماء من الرموز الممنوعة في Firebase
    def clean_key(text):
        for char in [".", "$", "#", "[", "]", "/", " "]:
            text = text.replace(char, "_")
        return text

    clean_league = clean_key(league_name)
    match_id = clean_key(f"{match_data['home_team']}_vs_{match_data['away_team']}")
    
    # الهيكلية الجديدة: التاريخ -> اسم الدوري -> المباراة
    url = f"{FIREBASE_URL}/{match_date}/{clean_league}/{match_id}.json"
    
    try:
        response = requests.put(url, json=match_data)
        if response.status_code == 200:
            print(f"✅ تم الحفظ: {league_name} - {match_data['home_team']}")
    except Exception as e:
        print(f"❌ خطأ Firebase: {e}")

def run_scraper():
    if not FIREBASE_URL:
        print("❌ خطأ: لم يتم ضبط FIREBASE_URL في Secrets!")
        return

    # الحصول على تاريخ اليوم بتنسيق YYYY-MM-DD
    today_date = datetime.now().strftime('%Y-%m-%d')
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
                    match_start_date = data.get('startDate').split('T')[0]
                    
                    # فلترة: جلب مباريات اليوم فقط
                    if match_start_date != today_date:
                        continue

                    match_url = data.get('url')
                    if not match_url.startswith("http"):
                        match_url = "https://www.kooora.com/" + match_url
                        
                    league = data.get('description', '').split(' - ')[0] or "دوري غير معروف"
                    home_team = data.get('homeTeam', {}).get('name')
                    away_team = data.get('awayTeam', {}).get('name')
                    
                    commentator, channel = get_match_details(match_url)
                    
                    match_info = {
                        "league": league,
                        "home_team": home_team,
                        "home_logo": data.get('homeTeam', {}).get('logo'),
                        "away_team": away_team,
                        "away_logo": data.get('awayTeam', {}).get('logo'),
                        "time": data.get('startDate'),
                        "commentator": commentator,
                        "channel": channel
                    }
                    
                    push_to_firebase(today_date, league, match_info)
                    count += 1
                    time.sleep(1) 
            except:
                continue
        print(f"🏁 العمليات المكتملة لليوم ({today_date}): {count}")
    except Exception as e:
        print(f"❌ خطأ رئيسي: {e}")

if __name__ == "__main__":
    run_scraper()
