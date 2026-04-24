import feedparser
import json
import time
import requests
import logging
import re
import unicodedata
from datetime import datetime
from pathlib import Path

from config import *

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


# -----------------------------
# تحميل الوظائف اللي اتشافت
# -----------------------------
def load_seen():
    if Path(SEEN_JOBS_FILE).exists():
        with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()


def save_seen(seen):
    with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(seen), f, ensure_ascii=False)


# -----------------------------
# تنظيف النص
# -----------------------------
def normalize(text):
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    return text.lower()


def clean_html(text):
    return re.sub(r"<[^>]+>", "", text)


# -----------------------------
# حساب الاسكور
# -----------------------------
def score_job(text):
    text = normalize(text)
    score = 0
    matched = []

    for k, v in KEYWORD_SCORES.items():
        if normalize(k) in text:
            score += v
            matched.append(k)

    if score == 0:
        score = 1

    return score, matched


# -----------------------------
# ارسال تليجرام
# -----------------------------
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        requests.post(url, json={
            "chat_id": TELEGRAM_CHAT_ID,
            "text": msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": True
        }, timeout=10)
    except Exception as e:
        log.error(f"Telegram error: {e}")


# -----------------------------
# تشغيل
# -----------------------------
def run():
    seen = load_seen()

    log.info("جلب الوظائف...")

    all_jobs = []

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)

        for entry in feed.entries:
            job_id = entry.get("id") or entry.get("link")

            title = entry.get("title", "")
            link = entry.get("link", "")
            summary = entry.get("summary", "")

            text = clean_html(title + " " + summary)

            all_jobs.append({
                "id": job_id,
                "title": title,
                "link": link,
                "text": text,
                "source": url
            })

    log.info(f"تم جلب {len(all_jobs)} وظيفة")

    new_jobs = [j for j in all_jobs if j["id"] not in seen]

    log.info(f"وظائف جديدة: {len(new_jobs)}")

    sent = 0

    for job in new_jobs:
        score, matched = score_job(job["text"] + job["title"])

        if score >= MIN_SCORE:
            msg = (
                f"🆕 <b>{job['title']}</b>\n"
                f"📌 المصدر: {job['source']}\n"
                f"⭐ الاسكور: {score}\n"
                f"🏷 الكلمات: {', '.join(matched) if matched else '—'}\n"
                f"🔗 {job['link']}"
            )

            send_telegram(msg)
            seen.add(job["id"])
            sent += 1
            time.sleep(0.5)

    save_seen(seen)

    if sent == 0:
        send_telegram("⚠️ مفيش شغل جديد أو كله متسجل قبل كده")

    log.info("خلصت الدورة")


# -----------------------------
# لوب مستمر
# -----------------------------
if __name__ == "__main__":
    run()
