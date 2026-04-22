import time
import json
import logging
import hashlib
import re
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup

# --- الإعدادات المباشرة (تأكد من صحة البيانات) ---
TELEGRAM_TOKEN = "8707793026:AAG0WZMRIb54ibbq0EDKGNlq75Q5Xok1NuA"
TELEGRAM_CHAT_ID = "1237819642"

# الكلمات المفتاحية الشاملة (تحليل بيانات + إدخال بيانات + سيرة ذاتية + كلمات عامة للصيد)
KEYWORDS = [
    "إدخال بيانات", "Data Entry", "تفريغ بيانات", "تفريغ محتوى", "نقل بيانات",
    "Power BI", "PowerBI", "تحليل بيانات", "Data Analyst", "Excel", "اكسل",
    "سيرة ذاتية", "CV", "سي في", "تعديل سيرة", "لينكد إن", "LinkedIn",
    "لوجو", "Logo", "شعار", "برزنتيشن", "PowerPoint", "بوربوينت",
    "مشروع", "مطلوب", "عمل", "وظيفة" # كلمات واسعة لضمان عمل البوت فوراً
]

SEEN_JOBS_FILE = "seen_jobs.json"
MAX_SEEN_JOBS = 1000

# إعداد اللوجز
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

def extract_budget(text):
    patterns = [r"[\$]\s?\d[\d,\.]*", r"\d[\d,\.]*\s?(USD|SAR|EGP|ريال|جنيه|دولار)"]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match: return match.group(0).strip()
    return "حسب الاتفاق"

def send_telegram(job):
    message = (
        f"🚀 *فرصة صيد جديدة يا هندسة!*\n\n"
        f"📌 *العنوان:* {job['title']}\n"
        f"💰 *الميزانية:* {job['budget']}\n"
        f"🌐 *المنصة:* {job['platform']}\n"
        f"🔗 [اضغط هنا للتقديم]({job['url']})\n"
        f"🕒 *الوقت:* {datetime.now().strftime('%H:%M')}"
    )
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=15)
    except Exception as e:
        log.error(f"Telegram Send Error: {e}")

def fetch_rss(url, name):
    jobs = []
    log.info(f"🔍 فحص منصة: {name}...")
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(resp.content, "xml")
        items = soup.find_all("item")
        for item in items:
            title = item.find("title").text if item.find("title") else "بدون عنوان"
            link = item.find("link").text if item.find("link") else ""
            desc_tag = item.find("description")
            desc = BeautifulSoup(desc_tag.text, "html.parser").get_text() if desc_tag else ""
            
            jobs.append({
                "title": title,
                "url": link,
                "description": desc,
                "platform": name,
                "budget": extract_budget(desc)
            })
    except Exception as e:
        log.error(f"Error fetching {name}: {e}")
    return jobs

def run_tracker():
    log.info("🚀 انطلاق رادارات الصيد...")
    
    # تحميل الوظائف المشاهدة سابقاً
    seen = set()
    if Path(SEEN_JOBS_FILE).exists():
        try:
            with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
                seen = set(json.load(f).get("seen", []))
        except: pass

    # المصادر الخمسة الكبرى (التي طلبتها)
    sources = [
        ("https://mostaql.com/projects/feed", "Mostaql"),
        ("https://khamsat.com/projects/feed", "Khamsat"),
        ("https://kafiil.com/feed/projects", "Kafiil"),
        ("https://baeed.com/feed", "Baeed"),
        ("https://nafezly.com/projects/feed", "Nafezly")
    ]
    
    all_jobs = []
    for url, name in sources:
        all_jobs.extend(fetch_rss(url, name))
    
    log.info(f"✅ تم سحب {len(all_jobs)} وظيفة إجمالاً.")

    new_count = 0
    for job in all_jobs:
        if not job["url"]: continue
        jid = hashlib.md5(job["url"].encode()).hexdigest()[:16]
        
        # دمج العنوان والوصف للبحث
        content = (job["title"] + " " + job["description"]).lower()
        
        # التحقق من الكلمات المفتاحية وأن الوظيفة لم ترسل من قبل
        if jid not in seen and any(kw.lower() in content for kw in KEYWORDS):
            send_telegram(job)
            seen.add(jid)
            new_count += 1
            time.sleep(1.5) # تجنب حظر تليجرام

    # حفظ الوظائف المشاهدة
    with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump({"seen": list(seen)[-MAX_SEEN_JOBS:]}, f)
        
    log.info(f"🏁 المهمة تمت. وجدت {new_count} وظائف جديدة مطابقة.")

if __name__ == "__main__":
    run_tracker()
