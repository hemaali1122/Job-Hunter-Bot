import requests
import time
from bs4 import BeautifulSoup

# --- بياناتك الشخصية (مدمجة لضمان العمل) ---
TOKEN = "8707793026:AAG0WZMRIb54ibbq0EDKGNlq75Q5Xok1NuA"
CHAT_ID = "1237819642"

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "Markdown"}
    try:
        r = requests.post(url, json=payload, timeout=15)
        return r.json() # عشان نشوف الرد في الـ Logs
    except Exception as e:
        return str(e)

def run():
    print("🚀 بدء عملية الفحص...")
    
    # 1. اختبار الاتصال (لازم يوصلك رسالة حالاً)
    res = send_telegram("🚨 إبراهيم! لو الرسالة دي وصلت، يبقى البوت شغال والـ ID سليم. جاري سحب المشاريع...")
    print(f"نتيجة اختبار تليجرام: {res}")

    # 2. فحص المنصات (هيجيب لك كل شيء بدون استثناء)
    sources = [
        ("https://mostaql.com/projects/feed", "Mostaql"),
        ("https://khamsat.com/projects/feed", "Khamsat"),
        ("https://kafiil.com/feed/projects", "Kafiil"),
        ("https://nafezly.com/projects/feed", "Nafezly")
    ]
    
    for url, name in sources:
        try:
            print(f"فحص {name}...")
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            soup = BeautifulSoup(r.content, "xml")
            items = soup.find_all("item")[:5] # هات آخر 5 مشاريع بس للتجربة
            
            for item in items:
                title = item.find("title").text
                link = item.find("link").text
                send_telegram(f"🔔 *مشروع من {name}*\n📌 {title}\n🔗 {link}")
                time.sleep(1)
        except Exception as e:
            print(f"خطأ في {name}: {e}")

if __name__ == "__main__":
    run()
