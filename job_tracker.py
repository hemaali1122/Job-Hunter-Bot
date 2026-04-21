"""
╔══════════════════════════════════════════════════════════════╗
║         Arabic Freelance Job Tracker + Telegram Alerts       ║
║         Supports: Mostaql, Khamsat, Wuzzuf                   ║
║         100% Free | Python Only                              ║
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

from config import (
    TELEGRAM_TOKEN,
    TELEGRAM_CHAT_ID,
    KEYWORDS,
    KEYWORD_SCORES,
    CHECK_INTERVAL_SECONDS,
    SEEN_JOBS_FILE,
    MAX_SEEN_JOBS,
)

# ─────────────────────────────────────────────
# Logging Setup
# ─────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("tracker.log", encoding="utf-8"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Seen Jobs Manager  (JSON file-based storage)
# ─────────────────────────────────────────────

def load_seen_jobs() -> set:
    """Load the set of previously seen job IDs from disk."""
    if Path(SEEN_JOBS_FILE).exists():
        with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(data.get("seen", []))
    return set()


def save_seen_jobs(seen: set) -> None:
    """Persist the seen job IDs to disk (trim to MAX_SEEN_JOBS)."""
    trimmed = list(seen)[-MAX_SEEN_JOBS:]
    with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump({"seen": trimmed, "updated": datetime.now().isoformat()}, f, ensure_ascii=False, indent=2)


def make_job_id(url: str) -> str:
    """Create a stable short ID from a job URL."""
    return hashlib.md5(url.strip().encode()).hexdigest()[:16]


# ─────────────────────────────────────────────
# Keyword Scoring
# ─────────────────────────────────────────────

def score_job(title: str, description: str) -> int:
    """
    Score a job based on keyword matches.
    Higher score = better match.
    Returns 0 if no keywords found (job should be skipped).
    """
    text = (title + " " + description).lower()
    total_score = 0
    for keyword, score in KEYWORD_SCORES.items():
        if keyword.lower() in text:
            total_score += score
    return total_score


def passes_keyword_filter(title: str, description: str) -> bool:
    """Return True if the job matches at least one configured keyword."""
    text = (title + " " + description).lower()
    return any(kw.lower() in text for kw in KEYWORDS)


# ─────────────────────────────────────────────
# Telegram Sender
# ─────────────────────────────────────────────

def send_telegram_message(job: dict) -> bool:
    """
    Send a formatted job alert to Telegram.
    Returns True on success.
    """
    score = job.get("score", 0)
    stars = "⭐" * min(score // 10, 5)  # visual score indicator

    message = (
        f"🚀 *New Job Found!*\n\n"
        f"📌 *Title:* {job['title']}\n"
        f"💰 *Budget:* {job.get('budget', 'Not specified')}\n"
        f"🌐 *Platform:* {job.get('platform', 'Unknown')}\n"
        f"📝 *Description:* {job.get('description', '')[:200]}...\n"
        f"🔗 *Link:* {job['url']}\n"
        f"🎯 *Relevance Score:* {score} {stars}\n"
        f"🕒 *Found at:* {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    )

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    }

    try:
        resp = requests.post(url, json=payload, timeout=15)
        if resp.status_code == 200:
            log.info(f"✅ Telegram alert sent: {job['title'][:60]}")
            return True
        else:
            log.warning(f"Telegram API error {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as e:
        log.error(f"Failed to send Telegram message: {e}")
        return False


# ─────────────────────────────────────────────
# Scraper: Mostaql  (RSS feed)
# ─────────────────────────────────────────────

def scrape_mostaql() -> list[dict]:
    """
    Fetch jobs from Mostaql using their public RSS feed.
    No API key required.
    """
    jobs = []
    rss_url = "https://mostaql.com/projects/feed"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; JobTrackerBot/1.0)"}

    try:
        resp = requests.get(rss_url, headers=headers, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "xml")

        for item in soup.find_all("item"):
            title = item.find("title").get_text(strip=True) if item.find("title") else ""
            url = item.find("link").get_text(strip=True) if item.find("link") else ""
            desc_raw = item.find("description").get_text(strip=True) if item.find("description") else ""
            # strip HTML tags from description
            description = BeautifulSoup(desc_raw, "html.parser").get_text(strip=True)

            # Try to extract budget from description
            budget = extract_budget(description)

            jobs.append({
                "title": title,
                "description": description[:400],
                "budget": budget,
                "url": url,
                "platform": "Mostaql",
            })

    except Exception as e:
        log.error(f"Mostaql scrape failed: {e}")

    log.info(f"Mostaql: fetched {len(jobs)} jobs")
    return jobs


# ─────────────────────────────────────────────
# Scraper: Khamsat  (RSS feed)
# ─────────────────────────────────────────────

def scrape_khamsat() -> list[dict]:
    """
    Fetch services from Khamsat using their public RSS feed.
    Khamsat is a micro-services marketplace (like Fiverr for Arabs).
    """
    jobs = []
    rss_url = "https://khamsat.com/services/feed"
    headers = {"User-Agent": "Mozilla/5.0 (compatible; JobTrackerBot/1.0)"}

    try:
        resp = requests.get(rss_url, headers=headers, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "xml")

        for item in soup.find_all("item"):
            title = item.find("title").get_text(strip=True) if item.find("title") else ""
            url = item.find("link").get_text(strip=True) if item.find("link") else ""
            desc_raw = item.find("description").get_text(strip=True) if item.find("description") else ""
            description = BeautifulSoup(desc_raw, "html.parser").get_text(strip=True)

            budget = extract_budget(description)

            jobs.append({
                "title": title,
                "description": description[:400],
                "budget": budget,
                "url": url,
                "platform": "Khamsat",
            })

    except Exception as e:
        log.error(f"Khamsat scrape failed: {e}")

    log.info(f"Khamsat: fetched {len(jobs)} jobs")
    return jobs


# ─────────────────────────────────────────────
# Scraper: Wuzzuf  (RSS feed)
# ─────────────────────────────────────────────

def scrape_wuzzuf() -> list[dict]:
    """
    Fetch jobs from Wuzzuf using their public RSS/search feed.
    We search for each keyword separately and merge results.
    """
    jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (compatible; JobTrackerBot/1.0)"}

    # Wuzzuf provides RSS per search query
    search_terms = ["data+analyst", "power+bi", "excel", "data+analysis"]

    seen_urls = set()
    for term in search_terms:
        rss_url = f"https://wuzzuf.net/search/jobs/feed/?q={term}&country=egypt"
        try:
            resp = requests.get(rss_url, headers=headers, timeout=20)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.content, "xml")

            for item in soup.find_all("item"):
                url = item.find("link").get_text(strip=True) if item.find("link") else ""
                if url in seen_urls:
                    continue
                seen_urls.add(url)

                title = item.find("title").get_text(strip=True) if item.find("title") else ""
                desc_raw = item.find("description").get_text(strip=True) if item.find("description") else ""
                description = BeautifulSoup(desc_raw, "html.parser").get_text(strip=True)
                budget = extract_budget(description)

                jobs.append({
                    "title": title,
                    "description": description[:400],
                    "budget": budget,
                    "url": url,
                    "platform": "Wuzzuf",
                })

        except Exception as e:
            log.error(f"Wuzzuf scrape failed for term '{term}': {e}")

    log.info(f"Wuzzuf: fetched {len(jobs)} jobs")
    return jobs


# ─────────────────────────────────────────────
# Utility: Budget Extractor
# ─────────────────────────────────────────────

def extract_budget(text: str) -> str:
    """
    Try to extract a budget/price mention from text.
    Handles SAR, EGP, USD, $ signs, and Arabic ريال/جنيه patterns.
    """
    patterns = [
        r"[\$＄]\s?\d[\d,\.]*",          # $500 or $1,000
        r"\d[\d,\.]*\s?(USD|SAR|EGP|KWD|AED)",  # 500 USD
        r"\d[\d,\.]*\s?(ريال|جنيه|دولار|دينار)",  # Arabic currency
        r"Budget[:\s]+[\$\d][\d,\.]*",    # Budget: $500
        r"ميزانية[:\s]+\d[\d,\.]*",       # Arabic "budget"
    ]
    for pat in patterns:
        match = re.search(pat, text, re.IGNORECASE | re.UNICODE)
        if match:
            return match.group(0).strip()
    return "Not specified"


# ─────────────────────────────────────────────
# Main Loop
# ─────────────────────────────────────────────

def run_tracker():
    """
    Main loop:
    1. Load seen job IDs.
    2. Fetch jobs from all platforms.
    3. Filter by keywords.
    4. Score and sort.
    5. Send Telegram alerts for new jobs.
    6. Save updated seen jobs.
    7. Sleep and repeat.
    """
    log.info("=" * 60)
    log.info("🚀 Arabic Job Tracker Started")
    log.info(f"   Keywords : {KEYWORDS}")
    log.info(f"   Interval : {CHECK_INTERVAL_SECONDS}s")
    log.info("=" * 60)

    # Quick Telegram connectivity test
    test_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe"
    try:
        r = requests.get(test_url, timeout=10)
        bot_info = r.json()
        if bot_info.get("ok"):
            log.info(f"✅ Telegram bot connected: @{bot_info['result']['username']}")
        else:
            log.error(f"❌ Telegram bot test failed: {bot_info}")
    except Exception as e:
        log.error(f"❌ Cannot reach Telegram: {e}")

    cycle = 0
    while True:
        cycle += 1
        log.info(f"\n--- Cycle #{cycle} | {datetime.now().strftime('%H:%M:%S')} ---")

        seen_jobs = load_seen_jobs()

        # Collect jobs from all platforms
        all_jobs = []
        all_jobs.extend(scrape_mostaql())
        all_jobs.extend(scrape_khamsat())
        all_jobs.extend(scrape_wuzzuf())

        log.info(f"Total fetched: {len(all_jobs)} jobs")

        # Filter → score → sort
        new_jobs = []
        for job in all_jobs:
            job_id = make_job_id(job["url"])
            if job_id in seen_jobs:
                continue  # already processed
            if not passes_keyword_filter(job["title"], job["description"]):
                continue  # doesn't match keywords
            job["score"] = score_job(job["title"], job["description"])
            job["id"] = job_id
            new_jobs.append(job)

        # Sort best matches first
        new_jobs.sort(key=lambda j: j["score"], reverse=True)

        log.info(f"New matching jobs: {len(new_jobs)}")

        for job in new_jobs:
            if send_telegram_message(job):
                seen_jobs.add(job["id"])
                time.sleep(1.5)  # small delay between messages to avoid Telegram rate limit

        save_seen_jobs(seen_jobs)
        log.info(f"Sleeping {CHECK_INTERVAL_SECONDS}s until next check…\n")
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    run_tracker()
