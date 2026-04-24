"""
RSS Job Feed Monitor with Telegram Notifications
=================================================
Production-ready script that:
- Monitors multiple RSS feeds for freelance jobs
- Supports Arabic content (UTF-8)
- Scores and filters jobs by keywords
- Persists seen jobs to avoid duplicates
- Sends rich Telegram messages
- Logs everything for easy debugging
"""

import feedparser
import json
import logging
import os
import re
import time
import unicodedata
from datetime import datetime
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# CONFIGURATION  ← Edit this section or move to config.py / .env
# ---------------------------------------------------------------------------

TELEGRAM_BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
TELEGRAM_CHAT_ID   = "YOUR_CHAT_ID_HERE"

# RSS feeds to monitor
RSS_FEEDS = [
    "https://www.upwork.com/ab/feed/jobs/rss?q=python&sort=recency",
    "https://www.freelancer.com/rss/jobs.xml",
    # Add more feeds here
]

# Keywords with scores (higher = more relevant)
KEYWORD_SCORES: dict[str, int] = {
    # High value
    "python":        10,
    "django":        10,
    "fastapi":       10,
    "flask":         8,
    "api":           8,
    "automation":    7,
    "scraping":      7,
    "data":          6,
    "backend":       6,
    # Arabic equivalents
    "بايثون":        10,
    "برمجة":         8,
    "تطوير":         6,
    "واجهة برمجية":  8,
    "أتمتة":         7,
    # Medium value
    "javascript":    5,
    "react":         5,
    "node":          5,
    # Low value / noise
    "freelance":     1,
    "remote":        1,
}

# Minimum score for a job to be sent to Telegram (0 = send all)
MIN_SCORE = 5

# File to persist seen job IDs/links
SEEN_JOBS_FILE = "seen_jobs.json"

# How often to run (seconds) — set to 0 to run once and exit
POLL_INTERVAL = 300  # 5 minutes

# ---------------------------------------------------------------------------
# LOGGING SETUP
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("rss_monitor.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# PERSISTENT STORAGE — seen jobs
# ---------------------------------------------------------------------------

def load_seen_jobs() -> set:
    """Load previously seen job identifiers from disk."""
    path = Path(SEEN_JOBS_FILE)
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            seen = set(data.get("seen", []))
            log.info("Loaded %d seen job IDs from %s", len(seen), SEEN_JOBS_FILE)
            return seen
        except (json.JSONDecodeError, KeyError) as exc:
            log.warning("Could not read %s (%s) — starting fresh.", SEEN_JOBS_FILE, exc)
    return set()


def save_seen_jobs(seen: set) -> None:
    """Persist seen job identifiers to disk."""
    with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump({"seen": list(seen), "updated": datetime.utcnow().isoformat()}, f, ensure_ascii=False, indent=2)
    log.debug("Saved %d seen job IDs.", len(seen))


# ---------------------------------------------------------------------------
# TEXT UTILITIES
# ---------------------------------------------------------------------------

def normalize_text(text: str) -> str:
    """
    Lowercase + normalize unicode so Arabic and Latin text both match cleanly.
    Preserves Arabic characters while stripping diacritics.
    """
    if not text:
        return ""
    # Normalize unicode (NFC keeps Arabic composed correctly)
    text = unicodedata.normalize("NFC", text)
    return text.lower()


def extract_text(entry: feedparser.FeedParserDict) -> str:
    """Extract all searchable text from a feed entry."""
    parts = []
    for field in ("title", "summary", "description", "content"):
        value = getattr(entry, field, None)
        if value is None:
            continue
        if isinstance(value, list):          # content field is a list of dicts
            for block in value:
                if isinstance(block, dict):
                    parts.append(block.get("value", ""))
                else:
                    parts.append(str(block))
        else:
            parts.append(str(value))
    # Strip HTML tags for clean text matching
    combined = " ".join(parts)
    combined = re.sub(r"<[^>]+>", " ", combined)   # remove HTML
    combined = re.sub(r"\s+", " ", combined).strip()
    return combined


# ---------------------------------------------------------------------------
# KEYWORD SCORING
# ---------------------------------------------------------------------------

def score_job(text: str) -> tuple[int, list[str]]:
    """
    Score a job entry against KEYWORD_SCORES.
    Returns (total_score, matched_keywords).
    Matching is:
      - Case-insensitive
      - Partial (substring) match
      - Unicode-normalized (handles Arabic)
    """
    normalized = normalize_text(text)
    total = 0
    matched = []
    for keyword, points in KEYWORD_SCORES.items():
        kw_norm = normalize_text(keyword)
        if kw_norm in normalized:
            total += points
            matched.append(keyword)
    return total, matched


# ---------------------------------------------------------------------------
# RSS PARSING
# ---------------------------------------------------------------------------

def fetch_feed(url: str) -> list[dict]:
    """
    Parse a single RSS/Atom feed using feedparser.
    Returns a list of job dicts.
    """
    log.info("Fetching feed: %s", url)
    try:
        feed = feedparser.parse(url)
    except Exception as exc:
        log.error("Exception parsing feed %s: %s", url, exc)
        return []

    if feed.bozo and feed.bozo_exception:
        # bozo=True means the feed is not well-formed, but entries may still be usable
        log.warning("Feed %s has markup issues: %s", url, feed.bozo_exception)

    entries = feed.entries
    log.info("  → %d entries found in feed", len(entries))

    jobs = []
    for entry in entries:
        # Unique identifier: prefer 'id', fall back to 'link', then title hash
        job_id = (
            getattr(entry, "id", None)
            or getattr(entry, "link", None)
            or str(hash(getattr(entry, "title", "")))
        )
        title = getattr(entry, "title", "No title")
        link  = getattr(entry, "link",  "No link")
        full_text = extract_text(entry)

        jobs.append({
            "id":        job_id,
            "title":     title,
            "link":      link,
            "text":      full_text,
            "source":    feed.feed.get("title", url),
        })

    return jobs


def fetch_all_feeds(feed_urls: list[str]) -> list[dict]:
    """Fetch and aggregate jobs from all configured feeds."""
    all_jobs = []
    for url in feed_urls:
        all_jobs.extend(fetch_feed(url))
    log.info("Total raw jobs fetched across all feeds: %d", len(all_jobs))
    return all_jobs


# ---------------------------------------------------------------------------
# FILTERING & DEDUPLICATION
# ---------------------------------------------------------------------------

def filter_new_jobs(jobs: list[dict], seen: set) -> tuple[list[dict], int]:
    """
    Remove already-seen jobs.
    Returns (new_jobs, duplicate_count).
    """
    new_jobs = []
    duplicates = 0
    for job in jobs:
        if job["id"] in seen:
            duplicates += 1
        else:
            new_jobs.append(job)
    log.info("New jobs (not seen before): %d | Duplicates skipped: %d", len(new_jobs), duplicates)
    return new_jobs, duplicates


def apply_scoring(jobs: list[dict], min_score: int) -> tuple[list[dict], int]:
    """
    Score each job and filter by MIN_SCORE.
    Returns (qualifying_jobs, filtered_out_count).
    """
    qualifying = []
    filtered_out = 0
    for job in jobs:
        score, matched = score_job(job["text"] + " " + job["title"])
        job["score"]   = score
        job["matched"] = matched
        if score >= min_score:
            qualifying.append(job)
        else:
            log.debug(
                "  FILTERED OUT (score=%d < %d): %s | keywords=%s",
                score, min_score, job["title"][:60], matched or "none"
            )
            filtered_out += 1

    log.info(
        "After scoring filter (min=%d): %d qualify | %d filtered out",
        min_score, len(qualifying), filtered_out
    )
    return qualifying, filtered_out


# ---------------------------------------------------------------------------
# TELEGRAM
# ---------------------------------------------------------------------------

def send_telegram(message: str) -> bool:
    """Send a message to Telegram. Returns True on success."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id":    TELEGRAM_CHAT_ID,
        "text":       message,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
    }
    try:
        resp = requests.post(url, json=payload, timeout=10)
        if resp.ok:
            log.debug("Telegram message sent successfully.")
            return True
        else:
            log.error("Telegram API error %d: %s", resp.status_code, resp.text[:200])
            return False
    except requests.RequestException as exc:
        log.error("Failed to send Telegram message: %s", exc)
        return False


def format_job_message(job: dict) -> str:
    """Format a single job as an HTML Telegram message."""
    matched_str = ", ".join(f"#{kw.replace(' ', '_')}" for kw in job["matched"]) or "—"
    return (
        f"🆕 <b>{job['title']}</b>\n"
        f"📌 <b>Source:</b> {job['source']}\n"
        f"⭐ <b>Score:</b> {job['score']}\n"
        f"🏷 <b>Keywords:</b> {matched_str}\n"
        f"🔗 <a href=\"{job['link']}\">View Job</a>"
    )


def send_summary(total_fetched: int, new_count: int, sent_count: int,
                 duplicates: int, filtered_out: int) -> None:
    """Send a diagnostic summary when no jobs are sent."""
    if sent_count > 0:
        return  # No need for a summary if jobs were sent
    if total_fetched == 0:
        reason = "⚠️ No jobs fetched — feeds may be empty, unreachable, or incorrectly configured."
    elif new_count == 0:
        reason = f"ℹ️ All {duplicates} fetched jobs were already seen (no new postings)."
    elif filtered_out > 0:
        reason = (
            f"ℹ️ {new_count} new job(s) found, but all were filtered out by keyword scoring "
            f"(min score = {MIN_SCORE}). Consider lowering MIN_SCORE or adding more keywords."
        )
    else:
        reason = "⚠️ Unknown reason — check rss_monitor.log for details."

    msg = f"📋 <b>RSS Monitor Report</b>\n{reason}"
    send_telegram(msg)
    log.info("Summary sent to Telegram: %s", reason)


# ---------------------------------------------------------------------------
# MAIN LOOP
# ---------------------------------------------------------------------------

def run_once() -> None:
    """One full fetch-filter-notify cycle."""
    log.info("=" * 60)
    log.info("Starting RSS monitor cycle — %s", datetime.utcnow().isoformat())

    seen = load_seen_jobs()

    # 1. Fetch
    all_jobs = fetch_all_feeds(RSS_FEEDS)

    # 2. Remove duplicates
    new_jobs, duplicates = filter_new_jobs(all_jobs, seen)

    # 3. Score & filter
    qualifying, filtered_out = apply_scoring(new_jobs, MIN_SCORE)

    # 4. Sort by score descending
    qualifying.sort(key=lambda j: j["score"], reverse=True)

    # 5. Send to Telegram
    sent = 0
    for job in qualifying:
        log.info("Sending job (score=%d): %s", job["score"], job["title"][:80])
        msg = format_job_message(job)
        if send_telegram(msg):
            seen.add(job["id"])
            sent += 1
            time.sleep(0.5)  # Avoid Telegram rate limits

    # Mark all new (even non-qualifying) as seen to avoid re-checking
    for job in new_jobs:
        seen.add(job["id"])

    save_seen_jobs(seen)

    log.info(
        "Cycle complete — fetched=%d | new=%d | sent=%d | duplicates=%d | filtered=%d",
        len(all_jobs), len(new_jobs), sent, duplicates, filtered_out
    )

    # 6. Notify if nothing was sent
    send_summary(len(all_jobs), len(new_jobs), sent, duplicates, filtered_out)


def main() -> None:
    log.info("RSS Job Monitor started. Poll interval: %ds | Min score: %d", POLL_INTERVAL, MIN_SCORE)
    if TELEGRAM_BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        log.warning("⚠️  TELEGRAM_BOT_TOKEN is not configured — Telegram messages will fail.")

    while True:
        try:
            run_once()
        except Exception as exc:
            log.exception("Unhandled exception in run_once(): %s", exc)

        if POLL_INTERVAL <= 0:
            log.info("POLL_INTERVAL=0, running once and exiting.")
            break

        log.info("Sleeping %d seconds until next cycle…", POLL_INTERVAL)
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main()
