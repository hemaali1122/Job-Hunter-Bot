# config.py
import os

TELEGRAM_TOKEN = "8707793026:AAG0WZMRIb54ibbq0EDKGNlq75Q5Xok1NuA"
TELEGRAM_CHAT_ID = "1237819642"

# كلمات البحث (ضفت لك كلمات عامة جداً للاختبار النهائي)
KEYWORDS = [
    "مشروع", "مطلوب", "عمل", "وظيفة", "بيانات", "تعديل", "تصميم",
    "إدخال بيانات", "Data Entry", "Power BI", "Excel", "اكسل", "سيرة ذاتية"
]

KEYWORD_SCORES = {
    "Power BI": 40, "تحليل بيانات": 40, 
    "إدخال بيانات": 30, "Excel": 20,
    "مشروع": 5, "مطلوب": 5
}

CHECK_INTERVAL_SECONDS = 300
SEEN_JOBS_FILE = "seen_jobs.json"
MAX_SEEN_JOBS = 1000
