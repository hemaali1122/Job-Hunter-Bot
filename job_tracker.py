import requests
import time
from bs4 import BeautifulSoup
import logging

# إعداد اللوجز
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# --- بياناتك الشخصية ---
TOKEN = "8707793026:AAG0WZMRIb54ibbq0EDKGNlq75Q5Xok1NuA"
CHAT_ID = "1237819642"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=15)
    except:
        pass

def run():
    log.info("🚀 رادار الصيد الشامل بدأ العمل...")
    
    # رسالة ترحيب لبدء الفحص
    send_telegram("📡 *بدء عملية مسح شاملة لكافة المنصات الآن...*")

    # الروابط الرسمية للـ RSS
    sources = [
        ("https://mostaql.com/projects/feed", "Mostaql - مستقل"),
        ("https://khamsat.com/projects/feed", "Khamsat - خمسات"),
        ("https://kafiil.com/feed/projects", "Kafiil - كفيل"),
        ("https://nafezly.com/projects/feed", "Nafezly - نفذلي"),
        ("https://baeed.com/feed", "Baeed - بعيد")
    ]
    
    found_total = 0
    for rss_url, name in sources:
        try:
            log.info(f"فحص منصة {name}...")
            # استخدام User-Agent عشان المواقع متفتكرناش بوتات وتعمل بلوك
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            r = requests.get(rss_url, headers=headers, timeout=20)
            
            if r.status_code == 200:
                soup = BeautifulSoup(r.content, "xml")
                items = soup.find_all("item")
                
                # هناخد أول 5 مشاريع "فقط" من كل موقع عشان موبايلك ميهنجش في أول تجربة
                for item in items[:5]:
                    title = item.find("title").text
                    link = item.find("link").text
                    
                    msg = f"🔔 *مشروع متاح الآن!*\n\n📌 *العنوان:* {title}\n🌐 *المنصة:* {name}\n🔗 [اضغط هنا للتقديم]({link})"
                    send_telegram(msg)
                    found_total += 1
                    time.sleep(1.5) # تأخير بسيط لضمان وصول الرسائل بالترتيب
            else:
                log.warning(f"تعذر الوصول لـ {name}، كود الحالة: {r.status_code}")
        except Exception as e:
            log.error(f"خطأ في {name}: {e}")

    send_telegram(f"🏁 *تم الانتهاء من المسح الشامل.*\nوجدنا {found_total} مشروع متاح للتقديم حالياً.")

if __name__ == "__main__":
    run()
