import requests
import hashlib
from bs4 import BeautifulSoup
import time

# --- إعداداتك المباشرة ---
TOKEN = "8707793026:AAG0WZMRIb54ibbq0EDKGNlq75Q5Xok1NuA"
CHAT_ID = "1237819642"
# كلمات بحث "واسعة جداً" عشان نضمن إنه يلقط أي حاجة
KEYWORDS = ["مشروع", "مطلوب", "عمل", "بيانات", "تصميم", "اكسل"]

def send_test():
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": "🚨 يا إبراهيم! لو قريت الرسالة دي يبقى السيستم شغال والاتصال سليم 100%.. جاري البحث عن وظائف الآن 👇",
        "parse_mode": "Markdown"
    }
    requests.post(url, json=payload)

def run():
    send_test() # بيبعت رسالة أول ما يشتغل فوراً
    
    # المواقع
    urls = [
        ("https://mostaql.com/projects/feed", "Mostaql"),
        ("https://khamsat.com/projects/feed", "Khamsat"),
        ("https://kafiil.com/feed/projects", "Kafiil")
    ]
    
    for rss_url, name in urls:
        try:
            r = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            soup = BeautifulSoup(r.content, "xml")
            items = soup.find_all("item")
            
            for item in items:
                title = item.find("title").text
                link = item.find("link").text
                # لو أي كلمة من الكلمات موجودة في العنوان
                if any(kw.lower() in title.lower() for kw in KEYWORDS):
                    msg = f"✅ لقطنا شغلانة جديدة!\n📌 المنصة: {name}\n🔗 الرابط: {link}"
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                                  json={"chat_id": CHAT_ID, "text": msg})
                    time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    run()
