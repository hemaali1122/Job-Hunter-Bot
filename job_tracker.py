import time, json, logging, hashlib, re, requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from config import TELEGRAM_TOKEN, TELEGRAM_CHAT_ID, KEYWORDS, KEYWORD_SCORES, SEEN_JOBS_FILE, MAX_SEEN_JOBS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

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
        r = requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}, timeout=15)
        if r.status_code != 200: log.error(f"Telegram error: {r.text}")
    except Exception as e: log.error(f"Send failed: {e}")

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
            jobs.append({"title": title, "url": link, "description": desc, "platform": name, "budget": extract_budget(desc)})
    except: pass
    return jobs

def run_tracker():
    log.info("🚀 رادارات الصيد تعمل الآن...")
    seen = set()
    if Path(SEEN_JOBS_FILE).exists():
        try:
            with open(SEEN_JOBS_FILE, "r", encoding="utf-8") as f:
                seen = set(json.load(f).get("seen", []))
        except: pass

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
    
    new_matches = []
    for job in all_jobs:
        jid = hashlib.md5(job["url"].encode()).hexdigest()[:16]
        text = (job["title"] + " " + job["description"]).lower()
        if jid not in seen and any(kw.lower() in text for kw in KEYWORDS):
            job["score"] = sum(score for kw, score in KEYWORD_SCORES.items() if kw.lower() in text)
            job["id"] = jid
            new_matches.append(job)

    for job in sorted(new_matches, key=lambda x: x["score"], reverse=True):
        send_telegram(job)
        seen.add(job["id"])
        time.sleep(1)

    with open(SEEN_JOBS_FILE, "w", encoding="utf-8") as f:
        json.dump({"seen": list(seen)[-MAX_SEEN_JOBS:]}, f)
    log.info(f"✅ تم الانتهاء. وجدنا {len(new_matches)} وظيفة جديدة.")

if __name__ == "__main__":
    run_tracker()
