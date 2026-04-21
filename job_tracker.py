# job_tracker.py
import time
import json
import logging
import hashlib
import re
from datetime import datetime
from pathlib import Path
import requests
from bs4 import BeautifulSoup

from config import (
    TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, KEYWORDS, 
    KEYWORD_SCORES, SEEN_JOBS_FILE, MAX_SEEN_JOBS
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

def load_seen_jobs():
    if Path(SEEN_JOBS_FILE).exists():
        try:
            with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f).get("seen", []))
        except: return set()
    return set()

def save_seen_jobs(seen):
    trimmed = list(seen)[-MAX_SEEN_JOBS:]
    with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump({"seen": trimmed}, f)

def make_job_id(url):
    return hashlib.md5(url.encode()).hexdigest()[:16]

def extract_budget(text):
    patterns = [r"[\$]\s?\d[\d,\.]*", r"\d[\d,\.]*\s?(USD|SAR|EGP|ريال|جنيه|دولار)"]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match: return match.group(0).strip()
    return "حسب الاتفاق"

def send_telegram(job):
    score = job.get("score", 0)
    stars = "⭐" * min(max(score // 10, 1), 5)
    message = (
        f"🚀 *فرصة صيد جديدة يا هندسة!*\n\n"
        f"📌 *العنوان:* {job['title']}\n"
        f"💰 *الميزانية:* {job['budget']}\n"
        f"🌐 *المنصة:* {job['platform']}\n"
        f"🎯 *التقييم:* {score} {stars}\n"
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
            title = item.find("title").text if item.find("title") else "بدون عنوان"
            link = item.find("link").text if item.find("link") else ""
            desc_tag = item.find("description")
            desc = BeautifulSoup(desc_tag.text, "html.parser").get_text() if desc_tag else ""
            jobs.append({"title": title, "url": link, "description": desc, "platform": name, "budget": extract_budget(desc)})
    except: pass
    return jobs

def run_tracker():
    log.info("🚀 رادارات الصيد تعمل الآن على كافة المنصات...")
    seen = load_seen_jobs()
    
    # القائمة المحدثة للمنصات (مستقل، خمسات، كفيل، بعيد، نفذلي)
    sources = [
        ("https://mostaql.com/projects/feed", "Mostaql"),
        ("https://khamsat.com/projects/feed", "Khamsat"),
        ("https://kafiil.com/feed/projects", "Kafiil"),
        ("https://baeed.com/feed", "Baeed"),
        ("https://nafezly.com/projects/feed", "Nafezly") # منصة نفذلي
    ]
    
    all_jobs = []
    for url, name in sources: 
        all_jobs.extend(fetch_rss(url, name))
    
    # Wuzzuf (تعديل الروابط لضمان عدم حدوث 404)
    for term in ["data-entry", "excel", "power-bi", "graphic-design"]:
        all_jobs.extend(fetch_rss(f"https://wuzzuf.net/search/jobs/feed/?q={term}", "Wuzzuf"))

    new_matches = []
    for job in all_jobs:
        if not job["url"]: continue
        jid = make_job_id(job["url"])
        text = (job["title"] + " " + job["description"]).lower()
        if jid not in seen and any(kw.lower() in text for kw in KEYWORDS):
            job["score"] = sum(score for kw, score in KEYWORD_SCORES.items() if kw.lower() in text)
            job["id"] = jid
            new_matches.append(job)

    for job in sorted(new_matches, key=lambda x: x["score"], reverse=True):
        send_telegram(job)
        seen.add(job["id"])
        time.sleep(2)

    save_seen_jobs(seen)
    log.info(f"✅ تم الفحص. وجدنا {len(new_matches)} وظائف جديدة.")

if __name__ == "__main__":
    run_tracker()
