# config.py

TELEGRAM_BOT_TOKEN = "8707793026:AAG0WZMRIb54ibbq0EDKGNlq75Q5Xok1NuA"
TELEGRAM_CHAT_ID   = "1237819642"

# مصادر RSS (ضفت لك العربية كمان)
RSS_FEEDS = [
    "https://mostaql.com/projects/feed",
    "https://khamsat.com/projects/feed",
    "https://kafiil.com/feed/projects",
    "https://nafezly.com/projects/feed",
    "https://www.freelancer.com/rss/jobs.xml"
]

# كلمات البحث
KEYWORD_SCORES = {
    "excel": 10,
    "data": 10,
    "analysis": 10,
    "power bi": 15,
    "python": 15,
    "scraping": 10,

    # عربي
    "اكسل": 10,
    "تحليل": 10,
    "بيانات": 10,
    "بايثون": 15,
    "ادخال بيانات": 10,
    "تصميم": 5,
    "تعديل": 5
}

# مهم: خليناه صفر عشان يجيب كل الشغل
MIN_SCORE = 0

POLL_INTERVAL = 300
SEEN_JOBS_FILE = "seen_jobs.json"
