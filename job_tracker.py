import requests
from bs4 import BeautifulSoup
import time
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# --- بياناتك ---
TOKEN = "8707793026:AAG0WZMRIb54ibbq0EDKGNlq75Q5Xok1NuA"
CHAT_ID = "1237819642"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=15)
    except: pass

def run():
    send_telegram("📡 *بدء عملية الصيد من الروابط الرسمية (RSS)... جاري جلب المشاريع الآن!*")
    
    # الروابط الرسمية التي لا يمكن حظرها بسهولة
    sources = [
        ("https://mostaql.com/projects/feed", "Mostaql - مستقل"),
        ("https://khamsat.com/projects/feed", "Khamsat - خمسات"),
        ("https://kafiil.com/feed/projects", "Kafiil - كفيل"),
        ("https://nafezly.com/projects/feed", "Nafezly - نفذلي")
    ]
    
    found_total = 0
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

    for rss_url, name in sources:
        try:
            log.info(f"فحص {name}...")
            r = requests.get(rss_url, headers=headers, timeout=20)
            if r.status_code == 200:
                # نستخدم 'xml' لأن الروابط دي بتخرج بيانات بصيغة XML
                soup = BeautifulSoup(r.content, "xml")
                items = soup.find_all("item")
                
                for item in items[:10]: # هات أول 10 مشاريع من كل موقع
                    title = item.find("title").text.strip()
                    link = item.find("link").text.strip()
                    
                    send_telegram(f"🔥 *مشروع جديد من {name}*\n📌 {title}\n🔗 [اضغط للتقديم]({link})")
                    found_total += 1
                    time.sleep(1) # تأخير لضمان وصول الرسائل
            else:
                log.error(f"فشل الوصول لـ {name}: {r.status_code}")
        except Exception as e:
            log.error(f"خطأ في {name}: {e}")

    send_telegram(f"🏁 *انتهى الفحص!* وجدنا {found_total} مشروع متاح. لو الرقم لسه صفر، جرب تشغل الـ Action كمان 5 دقائق.")

if __name__ == "__main__":
    run()
