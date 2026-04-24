"""
مراقب وظائف الفريلانس — نسخة محسّنة
يدور على وظائف حقيقية ويبعتها على تيليجرام
"""

import feedparser
import requests
import json
import time
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

# =====================================================================
# ⚙️ الإعدادات — عدّل هنا
# =====================================================================

TELEGRAM_BOT_TOKEN = "ضع_التوكن_هنا"
TELEGRAM_CHAT_ID   = "ضع_الشات_ID_هنا"

# الكلمات المفتاحية اللي بتشتغل فيها مع النقاط
KEYWORD_SCORES = {
    # Python / Backend
    "python":       10,
    "django":       10,
    "flask":        10,
    "fastapi":      10,
    "bot":           8,
    "scraping":      8,
    "automation":    8,
    "api":           7,
    "backend":       7,
    "script":        6,

    # عربي
    "بايثون":       10,
    "برمجة":         8,
    "بوت":           8,
    "سكريبت":        7,
    "تطوير":         6,
    "واجهة":         5,
    "أتمتة":         8,
}

# أقل نقاط عشان الوظيفة تتبعت (صفر = ابعت كل حاجة)
MIN_SCORE = 1

# آخر كام ساعة تجيب منها وظائف (بدل is_today اللي كانت بتحذف كل حاجة)
HOURS_BACK = 72  # آخر 3 أيام — قلّلها لو عايز

# ملف حفظ الوظائف المشوفة (عشان ميتكررش)
SEEN_FILE = "seen_jobs.json"

# فيدات RSS — عدّلها حسب تخصصك
RSS_FEEDS = [
    # Upwork - Python
    "https://www.upwork.com/ab/feed/jobs/rss?q=python&sort=recency&paging=0%3B10",
    # Upwork - Django
    "https://www.upwork.com/ab/feed/jobs/rss?q=django&sort=recency&paging=0%3B10",
    # Upwork - Bot
    "https://www.upwork.com/ab/feed/jobs/rss?q=telegram+bot&sort=recency&paging=0%3B10",
    # Freelancer
    "https://www.freelancer.com/rss/jobs.xml",
    # مستقل
    "https://mostaql.com/projects/feed?category=software-development",
]

# =====================================================================
# LOGGING
# =====================================================================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("monitor.log", encoding="utf-8"),
    ]
)
log = logging.getLogger(__name__)

# =====================================================================
# حفظ الوظائف المشوفة
# =====================================================================

def load_seen() -> set:
    p = Path(SEEN_FILE)
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            seen = set(data.get("ids", []))
            log.info("✅ محمّل %d وظيفة مشوفة من القرص", len(seen))
            return seen
        except Exception as e:
            log.warning("⚠️ مش قادر يقرأ %s: %s", SEEN_FILE, e)
    return set()

def save_seen(seen: set):
    Path(SEEN_FILE).write_text(
        json.dumps({"ids": list(seen), "updated": datetime.utcnow().isoformat()},
                   ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

# =====================================================================
# تحليل الوقت
# =====================================================================

def is_recent(published_parsed) -> bool:
    """بدل is_today — بييجب آخر N ساعة بدل اليوم بس"""
    if not published_parsed:
        return True  # لو مفيش تاريخ، خليها تعدي (أفضل من ما تتحذفش)
    try:
        job_time = datetime(*published_parsed[:6], tzinfo=timezone.utc)
        cutoff   = datetime.now(timezone.utc) - timedelta(hours=HOURS_BACK)
        return job_time >= cutoff
    except Exception:
        return True  # في حالة error، خليها تعدي

# =====================================================================
# نظام النقاط
# =====================================================================

def score_job(title: str, description: str = "") -> tuple[int, list[str]]:
    """بيحسب نقاط الوظيفة ويرجع (المجموع، الكلمات اللي اتطابقت)"""
    text = (title + " " + description).lower()
    total = 0
    matched = []
    for kw, pts in KEYWORD_SCORES.items():
        if kw.lower() in text:
            total += pts
            matched.append(kw)
    return total, matched

# =====================================================================
# جلب الفيدات
# =====================================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; JobBot/1.0; +https://example.com)"
}

def fetch_feed(url: str) -> list[dict]:
    log.info("📡 بيفحص: %s", url)
    try:
        # feedparser بيعمل HTTP request لوحده، بنديله custom agent
        feed = feedparser.parse(url, request_headers=HEADERS)
    except Exception as e:
        log.error("❌ Error في الفيد %s: %s", url, e)
        return []

    if feed.bozo:
        log.warning("⚠️ فيد مش standard: %s | السبب: %s", url, feed.bozo_exception)

    entries = feed.entries
    feed_name = feed.feed.get("title", url[:50])
    log.info("   وجد %d وظيفة في '%s'", len(entries), feed_name)

    jobs = []
    for entry in entries:
        # ID فريد
        job_id = (
            getattr(entry, "id",   None) or
            getattr(entry, "link", None) or
            str(hash(entry.get("title", "")))
        )
        # وصف الوظيفة
        desc = ""
        if hasattr(entry, "summary"):
            desc = entry.summary
        elif hasattr(entry, "description"):
            desc = entry.description

        # إزالة HTML من الوصف
        import re
        desc_clean = re.sub(r"<[^>]+>", " ", desc)

        jobs.append({
            "id":        job_id,
            "title":     entry.get("title", "بدون عنوان"),
            "link":      entry.get("link",  "#"),
            "desc":      desc_clean[:300],
            "published": getattr(entry, "published_parsed", None),
            "source":    feed_name,
        })

    return jobs

# =====================================================================
# إرسال تيليجرام
# =====================================================================

def send_telegram(msg: str, parse_mode: str = "HTML") -> bool:
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, json={
            "chat_id":    TELEGRAM_CHAT_ID,
            "text":       msg,
            "parse_mode": parse_mode,
            "disable_web_page_preview": True,
        }, timeout=10)
        if not r.ok:
            log.error("❌ تيليجرام error %d: %s", r.status_code, r.text[:200])
        return r.ok
    except Exception as e:
        log.error("❌ فشل إرسال تيليجرام: %s", e)
        return False

def format_job(job: dict, score: int, matched: list[str]) -> str:
    kws = " ".join(f"#{k.replace(' ','_')}" for k in matched) if matched else "—"
    # اقصّر العنوان لو طويل
    title = job["title"][:100]
    return (
        f"🆕 <b>{title}</b>\n"
        f"📌 <b>المصدر:</b> {job['source']}\n"
        f"⭐ <b>النقاط:</b> {score}\n"
        f"🏷 <b>الكلمات:</b> {kws}\n"
        f"🔗 <a href=\"{job['link']}\">افتح الوظيفة</a>"
    )

# =====================================================================
# الدالة الرئيسية
# =====================================================================

def run():
    log.info("=" * 60)
    log.info("🚀 بدأ الفحص — %s", datetime.now().strftime("%Y-%m-%d %H:%M"))

    send_telegram(f"🔍 بدأ فحص الوظائف... (آخر {HOURS_BACK} ساعة)")

    seen = load_seen()

    stats = {
        "total_fetched":  0,
        "already_seen":   0,
        "too_old":        0,
        "low_score":      0,
        "sent":           0,
    }

    for url in RSS_FEEDS:
        jobs = fetch_feed(url)
        stats["total_fetched"] += len(jobs)

        for job in jobs:
            # 1. مشوفناها قبل كده؟
            if job["id"] in seen:
                stats["already_seen"] += 1
                log.debug("⏭ مكررة: %s", job["title"][:50])
                continue

            # 2. قديمة أوي؟
            if not is_recent(job["published"]):
                stats["too_old"] += 1
                seen.add(job["id"])
                log.debug("⏳ قديمة: %s", job["title"][:50])
                continue

            # 3. النقاط
            score, matched = score_job(job["title"], job["desc"])
            if score < MIN_SCORE:
                stats["low_score"] += 1
                seen.add(job["id"])
                log.debug("📉 نقاط قليلة (%d): %s", score, job["title"][:50])
                continue

            # ✅ وظيفة تستاهل — ابعتها!
            log.info("✅ إرسال (score=%d): %s", score, job["title"][:70])
            msg = format_job(job, score, matched)
            if send_telegram(msg):
                stats["sent"] += 1
                seen.add(job["id"])
                time.sleep(0.5)

    # حفظ الـ seen
    save_seen(seen)

    # ملخص
    log.info("📊 النتيجة: %s", stats)

    if stats["sent"] == 0:
        reasons = []
        if stats["already_seen"] > 0:
            reasons.append(f"• {stats['already_seen']} وظيفة مشوفناها قبل كده")
        if stats["too_old"] > 0:
            reasons.append(f"• {stats['too_old']} وظيفة قديمة (أكتر من {HOURS_BACK} ساعة)")
        if stats["low_score"] > 0:
            reasons.append(f"• {stats['low_score']} وظيفة منقطعتش (نقاط أقل من {MIN_SCORE})")
        if stats["total_fetched"] == 0:
            reasons.append("• مش قادر يجيب الفيدات — تحقق من الإنترنت أو الـ URLs")

        reason_text = "\n".join(reasons) if reasons else "• مجتش وظائف جديدة"
        summary = (
            f"📋 <b>تقرير الفحص</b>\n"
            f"🔢 إجمالي المجلوبة: {stats['total_fetched']}\n"
            f"📭 مفيش وظائف اتبعتت لأن:\n{reason_text}"
        )
        send_telegram(summary)
    else:
        send_telegram(f"✅ تم إرسال <b>{stats['sent']}</b> وظيفة جديدة!")

    log.info("=" * 60)

# =====================================================================

if __name__ == "__main__":
    run()
