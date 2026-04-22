import requests
from bs4 import BeautifulSoup
import time
import logging
import json
from pathlib import Path

# إعداد اللوجز
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# --- بياناتك الشخصية ---
TOKEN = "8707793026:AAG0WZMRIb54ibbq0EDKGNlq75Q5Xok1NuA"
CHAT_ID = "1237819642"
SEEN_JOBS_FILE = "seen_jobs.json"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except: pass

def run():
    log.info("🚀 رادار الصيد الشامل بدأ العمل...")
    
    # تحميل الذاكرة عشان ميبعتش الحاجة مرتين
    seen = set()
    if Path(SEEN_JOBS_FILE).exists():
        try:
            with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
                seen = set(json.load(f).get("seen", []))
        except: pass

    # المنصات اللي طلبتها في الصور
    sources = [
        ("https://mostaql.com/projects/feed", "مستقل"),
        ("https://khamsat.com/projects/feed", "خمسات"),
        ("https://kafiil.com/feed/projects", "كفيل"),
        ("https://nafezly.com/projects/feed", "نفذلي"),
        ("https://baeed.com/feed", "بعيد"),
        ("https://maatloob.com/projects/feed", "مطلوب") 
    ]
    
    new_jobs_found = 0
    for rss_url, name in sources:
        try:
            r = requests.get(rss_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            if r.status_code != 200: continue
            
            soup = BeautifulSoup(r.content, "xml")
            items = soup.find_all("item")
            
            for item in items:
                title = item.find("title").text
                link = item.find("link").text
                
                # هنا شلنا الفلترة (KEYWORDS) عشان يبعت كل حاجة
                if link not in seen:
                    msg = f"🔔 *مشروع جديد نزل الآن!*\n\n📌 *العنوان:* {title}\n🌐 *المنصة:* {name}\n🔗 [تفاصيل المشروع]({link})"
                    send_telegram(msg)
                    seen.add(link)
                    new_jobs_found += 1
                    time.sleep(1) # تأخير عشان تليجرام
        except: continue

    # حفظ الذاكرة (آخر 500 لينك عشان الملف ميكبرش)
    with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump({"seen": list(seen)[-500:]}, f)

    log.info(f"🏁 تم الفحص. وجدنا {new_jobs_found} مشاريع جديدة.")

if __name__ == "__main__":
    run()
