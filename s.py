from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

def get_kooora_debug():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    # تمويه إضافي للمتصفح
    chrome_options.add_argument("window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    driver_path = '/data/data/com.termux/files/usr/bin/chromedriver'

    try:
        driver = webdriver.Chrome(executable_path=driver_path, options=chrome_options)
        
        # الرابط المباشر لمباريات اليوم لضمان تحميل القسم الصحيح
        url = "https://www.kooora.com/?region=-1&area=0"
        driver.get(url)
        
        print("جاري فحص محتوى الصفحة...")
        time.sleep(10) # زيادة وقت الانتظار لضمان تحميل الـ Ajax

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        
        # محاولة البحث عن المباريات داخل الجداول (الهيكل الكلاسيكي لكووورة)
        matches = []
        
        # كووورة غالباً ما يستخدم جداول تحمل كلاس 'm_table' للمباريات
        tables = soup.find_all('table', class_='m_table')
        
        if not tables:
            # إذا لم يجد جداول، سنبحث عن أي عنصر يحتوي على كلمة 'vs' أو ' - ' بين فريقين
            print("لم يتم العثور على جداول مألوفة، جاري البحث عن هيكلية بديلة...")
            # فحص الـ match_box مجدداً ولكن بشكل أعمق
            items = soup.select('div[class*="match"]')
            print(f"تم العثور على {len(items)} عنصر مرشح لأن يكون مباراة.")
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                if 'match_row' in str(row.get('class', [])) or row.find('td', class_='match_time'):
                    try:
                        # استخراج البيانات بناءً على ترتيب الأعمدة
                        cols = row.find_all('td')
                        if len(cols) >= 3:
                            team_left = row.find('td', class_='team_left').text.strip()
                            team_right = row.find('td', class_='team_right').text.strip()
                            m_time = row.find('td', class_='match_time').text.strip()
                            
                            print(f"تم الجلب: {team_left} vs {team_right} في وقت {m_time}")
                            matches.append({
                                "team1": team_left,
                                "team2": team_right,
                                "time": m_time
                            })
                    except:
                        continue

        if not matches:
            # تصحيح الأخطاء: حفظ نسخة من الصفحة لرؤية ما يراه البوت
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            print("للأسف لم يتم العثور على بيانات. تم حفظ كود الصفحة في debug_page.html للفحص.")

        return matches

    except Exception as e:
        print(f"خطأ: {e}")
    finally:
        if 'driver' in locals():
            driver.quit()

get_kooora_debug()
