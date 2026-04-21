"""
╔══════════════════════════════════════════════════════════════╗
║     Arabic Multi-Platform Job Tracker (24/7 Edition)         ║
║   Supports: Mostaql, Khamsat, Wuzzuf, Kafiil, Baeed          ║
╚══════════════════════════════════════════════════════════════╝
"""

import time
import json
import logging
import hashlib
import os
import re
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# استيراد الإعدادات من ملف config
from config import (
    TELEGRAM_TOKEN,
    TELEGRAM_CHAT_ID,
    KEYWORDS,
    KEYWORD_SCORES,
    CHECK_INTERVAL_SECONDS,
    SEEN_JOBS_FILE,
    MAX_SEEN_JOBS,
)

# إعداد اللوجز (Logging)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# إدارة الوظائف المشاهدة (Seen Jobs)
# ─────────────────────────────────────────────

def load_seen_jobs() -> set:
    if Path(SEEN_JOBS_FILE).exists():
        try:
            with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return set(data.get("seen", []))
        except: return set()
    return set()

def save_seen_jobs(seen: set) -> None:
    trimmed = list(seen)[-MAX_SEEN_JOBS:]
    with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump({"seen": trimmed, "updated": datetime.now().isoformat()}, f)

def make_job_id(url: str) -> str:
    return hashlib.md5(url.strip().encode()).hexdigest()[:16]

# ─────────────────────────────────────────────
# نظام التقييم والفلترة
# ─────────────────────────────────────────────

def score_job(title: str, description: str) -> int:
    text = (title + " " + description).lower()
    total_score = 0
    for keyword, score in KEYWORD_SCORES.items():
        if keyword.lower() in text:
            total_score += score
    return total_score

def passes_keyword_filter(title: str, description: str) -> bool:
    text = (title + " " + description).lower()
    return any(kw.lower() in text for kw in KEYWORDS)

# ─────────────────────────────────────────────
# مرسل تليجرام
# ─────────────────────────────────────────────

def send_telegram_message(job: dict) -> bool:
    score = job.get("score", 0)
    stars = "⭐" * min(max(score // 10, 1), 5)

    message = (
        f"🚀 *فرصة عمل جديدة!*\n\n"
        f"📌 *العنوان:* {job['title']}\n"
        f"💰 *الميزانية:* {job.get('budget', 'غير محددة')}\n"
        f"🌐 *المنصة:* {job.get('platform', 'Unknown')}\n"
        f"📝 *الوصف:* {job.get('description', '')[:250]}...\n\n"
        f"🎯 *التقييم:* {score} {stars}\n"
        f"🔗 *الرابط:* [اضغط هنا للتقديم]({job['url']})\n"
        f"🕒 *الوقت:* {datetime.now().strftime('%H:%M')}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}

    try:
        resp = requests.post(url, json=payload, timeout=15)
        return resp.status_code == 200
    except: return False

# ─────────────────────────────────────────────
# دوال السحب (Scrapers) لكافة المواقع
# ─────────────────────────────────────────────

def fetch_rss(url, platform_name):
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        resp = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(resp.content, "xml")
        for item in soup.find_all("item"):
            title = item.find("title").text if item.find("title") else ""
            link = item.find("link").text if item.find("link") else ""
            desc_raw = item.find("description").text if item.find("description") else ""
            desc = BeautifulSoup(desc_raw, "html.parser").get_text(strip=True)
            
            jobs.append({
                "title": title,
                "description": desc,
                "url": link,
                "platform": platform_name,
                "budget": extract_budget(desc)
            })
    except Exception as e:
        log.error(f"Error fetching {platform_name}: {e}")
    return jobs

def extract_budget(text: str) -> str:
    patterns = [r"[\$]\s?\d[\d,\.]*", r"\d[\d,\.]*\s?(USD|SAR|EGP|ريال|جنيه|دولار)"]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE)
        if match: return match.group(0).strip()
    return "حسب الاتفاق"

# ─────────────────────────────────────────────
# المحرك الأساسي (Main Engine)
# ─────────────────────────────────────────────

def run_tracker():
    log.info("🚀 جاري تشغيل صياد الوظائف العربي...")
    seen_jobs = load_seen_jobs()

    # قائمة الروابط الشاملة
    sources = [
        ("https://mostaql.com/projects/feed", "Mostaql"),
        ("https://khamsat.com/projects/feed", "Khamsat"),
        ("https://kafiil.com/feed/projects", "Kafiil"),
        ("https://baeed.com/feed", "Baeed")
    ]

    all_jobs = []
    for url, name in sources:
        all_jobs.extend(fetch_rss(url, name))

    # إضافة وظائف Wuzzuf (بحث مخصص)
    wuzzuf_terms = ["data", "entry", "excel", "analysis"]
    for term in wuzzuf_terms:
        all_jobs.extend(fetch_rss(f"https://wuzzuf.net/search/jobs/feed/?q={term}", "Wuzzuf"))

    log.info(f"🔍 تم سحب {len(all_jobs)} وظيفة محتملة")

    new_matches = []
    for job in all_jobs:
        jid = make_job_id(job["url"])
        if jid not in seen_jobs and passes_keyword_filter(job["title"], job["description"]):
            job["score"] = score_job(job["title"], job["description"])
            job["id"] = jid
            new_matches.append(job)

    # ترتيب حسب الأهمية
    new_matches.sort(key=lambda x: x["score"], reverse=True)

    for job in new_matches:
        if send_telegram_message(job):
            seen_jobs.add(job["id"])
            time.sleep(2) # تأخير لتجنب الحظر

    save_seen_jobs(seen_jobs)
    log.info(f"✅ تم الانتهاء. وجدنا {len(new_matches)} وظيفة جديدة.")

if __name__ == "__main__":
    run_tracker()
