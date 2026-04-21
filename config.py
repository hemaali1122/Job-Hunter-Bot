# config.py
import os

TELEGRAM_TOKEN = "8707793026:AAG0WZMRIb54ibbq0EDKGNlq75Q5Xok1NuA"
TELEGRAM_CHAT_ID = "1237819642"

KEYWORDS = [
    "إدخال بيانات", "Data Entry", "تفريغ بيانات", "تفريغ محتوى", "نقل بيانات", "تجميع بيانات",
    "سيرة ذاتية", "CV", "سي في", "تعديل سيرة", "لينكد إن", "LinkedIn",
    "لوجو", "Logo", "شعار", "برزنتيشن", "Presentation", "بوربوينت", "PowerPoint",
    "ويب سايت", "وردبريس", "WordPress", "صفحة هبوط", "Landing Page",
    "تحليل بيانات", "Data Analyst", "اكسل", "Excel", "وورد", "Word", 
    "بور بي اي", "Power BI", "PowerBI", "بيثون", "Python", "SQL"
]

KEYWORD_SCORES = {
    "Power BI": 30, "PowerBI": 30, "تحليل بيانات": 30, "Data Analyst": 30,
    "سيرة ذاتية": 25, "CV": 25, "إدخال بيانات": 20, "Data Entry": 20,
    "Excel": 15, "اكسل": 15, "Logo": 15, "لوجو": 15
}

CHECK_INTERVAL_SECONDS = 300
SEEN_JOBS_FILE = "seen_jobs.json"
MAX_SEEN_JOBS = 1000
