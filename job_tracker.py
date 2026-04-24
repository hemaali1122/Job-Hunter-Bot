import feedparser
import requests
from datetime import datetime, timezone
import time

from config import *

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    requests.post(url, json={
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "disable_web_page_preview": True
    })


def is_today(published):
    if not published:
        return False

    try:
        job_time = datetime(*published[:6], tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)

        return job_time.date() == now.date()
    except:
        return False


def run():
    send_telegram("🚀 بدأ فحص شغل النهارده...")

    total_today = 0

    for url in RSS_FEEDS:
        feed = feedparser.parse(url)

        send_telegram(f"📡 فحص: {url}")

        for entry in feed.entries:
            if is_today(entry.get("published_parsed")):
                title = entry.get("title", "")
                link = entry.get("link", "")

                msg = f"🆕 شغل جديد اليوم:\n{title}\n{link}"

                send_telegram(msg)
                total_today += 1
                time.sleep(0.3)

    if total_today == 0:
        send_telegram("❌ مفيش شغل نازل النهارده في المصادر دي")

    else:
        send_telegram(f"✅ تم العثور على {total_today} شغل النهارده")


if __name__ == "__main__":
    run()
