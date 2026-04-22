import time
import json
import logging
import hashlib
import re
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

# --- إعداداتك الخاصة ---
TELEGRAM_TOKEN = "8707793026:AAG0WZMRIb54ibbq0EDKGNlq75Q5Xok1NuA"
TELEGRAM_CHAT_ID = "1237819642"

# الكلمات المفتاحية
KEYWORDS = [
    "Power BI", "PowerBI", "باور بي اي", "تحليل بيانات", "Data Analyst", 
    "إدخال بيانات", "Data Entry", "تفريغ بيانات", "تجميع بيانات",
    "اكسل", "Excel", "جداول بيانات", "سيرة ذاتية", "CV"
]

SEEN_JOBS_FILE = "seen_jobs.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

def send_telegram(job):
    message = (
        f"🎯 *مشروع متاح حالياً يا إبراهيم!*\n\n"
        f"📌 *العنوان:* {job['title']}\n"
        f"💰 *الميزانية:* {job['budget']}\n"
        f"🌐 *المنصة:* {job['platform']}\n\n"
        f"🔗 [اضغط هنا للتقديم]({job['url']})"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=15)
    except: pass

def fetch_rss(url, name):
    jobs = []
    try:
        resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        soup = BeautifulSoup(resp.content, "xml")
        for item in soup.find_all("item"):
            title = item.find("title").text if item.find("title") else ""
            link = item.find("link").text if item.find("link") else ""
            desc_raw = item.find("description").text if item.find("description") else ""
            desc = BeautifulSoup(desc_raw, "html.parser").get_text()
            jobs.append({"title": title, "url": link, "description": desc, "platform": name, "budget": "مشاهدة في الموقع"})
    except: pass
    return jobs

def run_tracker():
    log.info("🚀 جاري جلب كل المشاريع المتاحة حالياً...")
    
    # --- حركة تصفير الذاكرة عشان يبعت لك المتاح دلوقتي حالاً ---
    seen = set() # بنبدأ بذاكرة فاضية في كل لفة تجريبية
    
    sources = [
        ("https://mostaql.com/projects/feed", "Mostaql"),
        ("https://nafezly.com/projects/feed", "Nafezly"),
        ("https://kafiil.com/feed/projects", "Kafiil"),
        ("https://khamsat.com/projects/feed", "Khamsat")
    ]
    
    all_jobs = []
    for url, name in sources:
        all_jobs.extend(fetch_rss(url, name))
    
    sent_count = 0
    for job in all_jobs:
        content = (job["title"] + " " + job["description"]).lower()
        if any(kw.lower() in content for kw in KEYWORDS):
            send_telegram(job)
            sent_count += 1
            time.sleep(1) # تأخير بسيط عشان تليجرام ميعملش بلوك
            if sent_count > 10: break # كفاية 10 مشاريع للتجربة عشان الموبايل ميهنجش

    log.info(f"✅ تم إرسال {sent_count} مشروع لموبايلك.")

if __name__ == "__main__":
    run_tracker()
