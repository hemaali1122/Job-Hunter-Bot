import requests
from bs4 import BeautifulSoup
import time
import logging

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

TOKEN = "8707793026:AAG0WZMRIb54ibbq0EDKGNlq75Q5Xok1NuA"
CHAT_ID = "1237819642"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        requests.post(url, json={"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}, timeout=15)
    except: pass

def run():
    send_telegram("🚀 *بدء هجوم الصيد الشامل.. جاري اختراق حواجز المنصات وسحب المشاريع الآن!*")
    
    sources = [
        ("https://mostaql.com/projects", "مستقل"),
        ("https://nafezly.com/projects", "نفذلي"),
        ("https://kafiil.com/projects", "كفيل")
    ]
    
    found_total = 0
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
    }

    for url, name in sources:
        try:
            log.info(f"Scanning {name}...")
            r = requests.get(url, headers=headers, timeout=25)
            soup = BeautifulSoup(r.content, "html.parser")
            
            # محرك بحث ذكي حسب هيكلة كل موقع
            links = []
            if name == "مستقل":
                links = soup.select("h3 a")[:10]
            elif name == "نفذلي":
                links = soup.select("h2 a")[:10]
            elif name == "كفيل":
                links = soup.select("h3 a")[:10]

            for link in links:
                title = link.get_text().strip()
                href = link.get("href")
                if not href.startswith("http"):
                    base = "https://mostaql.com" if name == "مستقل" else "https://nafezly.com" if name == "نفذلي" else "https://kafiil.com"
                    href = base + href
                
                send_telegram(f"💎 *فرصة جديدة من {name}*\n📌 {title}\n🔗 [اضغط للتقديم]({href})")
                found_total += 1
                time.sleep(2)
        except Exception as e:
            log.error(f"Error in {name}: {e}")

    send_telegram(f"🏁 *انتهت الغارة بنجاح!* وجدنا {found_total} مشروع متاح حالياً. استعد للتقديم يا هندسة!")

if __name__ == "__main__":
    run()
