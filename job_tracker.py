import requests
import hashlib
from bs4 import BeautifulSoup
import time
import logging

# إعداد اللوجز عشان نشوف المشكلة فين في الـ Actions
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# --- إعداداتك المباشرة ---
TOKEN = "8707793026:AAG0WZMRIb54ibbq0EDKGNlq75Q5Xok1NuA"
CHAT_ID = "1237819642"

# كلمات بحث "واسعة جداً" للتجربة
KEYWORDS = ["مشروع", "مطلوب", "عمل", "بيانات", "تصميم", "اكسل", "Power"]

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=10)
        return r.json()
    except Exception as e:
        return str(e)

def run():
    log.info("🚀 بدء فحص الاتصال...")
    # رسالة تجربة إجبارية أول ما يشتغل
    test_res = send_telegram("🚨 يا إبراهيم! لو قريت الرسالة دي يبقى السيستم شغال والاتصال سليم 100%.. جاري البحث عن وظائف الآن 👇")
    log.info(f"Test message result: {test_res}")
    
    # الروابط
    urls = [
        ("https://mostaql.com/projects/feed", "Mostaql"),
        ("https://nafezly.com/projects/feed", "Nafezly"),
        ("https://kafiil.com/feed/projects", "Kafiil")
    ]
    
    found_any = False
    for rss_url, name in urls:
        try:
            log.info(f"Checking {name}...")
            r = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            soup = BeautifulSoup(r.content, "xml")
            items = soup.find_all("item")
            
            for item in items:
                title = item.find("title").text
                link = item.find("link").text
                # فحص الكلمات
                if any(kw.lower() in title.lower() for kw in KEYWORDS):
                    msg = f"✅ لقطنا شغلانة من {name}!\n📌 العنوان: {title}\n🔗 الرابط: {link}"
                    send_telegram(msg)
                    found_any = True
                    time.sleep(1)
        except Exception as e:
            log.error(f"Error in {name}: {e}")

    if not found_any:
        send_telegram("🧐 بحثت في المنصات ومالقيتش مشاريع جديدة مطابقة للكلمات حالياً.")

if __name__ == "__main__":
    run()
