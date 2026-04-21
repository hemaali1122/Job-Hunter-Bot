"""
config.py — Central configuration for the Arabic Job Tracker
═══════════════════════════════════════════════════════════
Edit this file to customize keywords, Telegram credentials,
check interval, and scoring weights.
"""

# ─────────────────────────────────────────────
# 🤖  TELEGRAM SETTINGS
#     1. Create a bot at https://t.me/BotFather
#     2. Copy the token it gives you → TELEGRAM_TOKEN
#     3. Start your bot, then visit:
#        https://api.telegram.org/bot<TOKEN>/getUpdates
#        to find your chat_id → TELEGRAM_CHAT_ID
# ─────────────────────────────────────────────
TELEGRAM_TOKEN   = "8707793026:AAG0WZMRIb54ibbq0EDKGNlq75Q5Xok1NuA"       # e.g. "7123456789:AAF..."
TELEGRAM_CHAT_ID = "1237819642"         # e.g. "123456789"  (personal) or "-1001234..." (group)


# ─────────────────────────────────────────────
# 🔍  KEYWORDS  (job must contain at least one)
#     Arabic and English terms both work.
# ─────────────────────────────────────────────
KEYWORDS = [
    # English
    "Data Analyst",
    "Data Analysis",
    "Excel",
    "Power BI",
    "PowerBI",
    "Dashboard",
    "Tableau",
    "SQL",
    "Python",
    "Reporting",
    "Business Intelligence",
    "BI",
    # Arabic
    "تحليل بيانات",
    "محلل بيانات",
    "اكسل",
    "لوحة تحكم",
    "تقارير",
    "ذكاء اعمال",
    "قواعد بيانات",
]


# ─────────────────────────────────────────────
# 🎯  KEYWORD SCORING
#     Higher score = better match = sent first.
#     Tune these weights to your priorities.
# ─────────────────────────────────────────────
KEYWORD_SCORES = {
    "Power BI":            30,
    "PowerBI":             30,
    "Data Analyst":        25,
    "Data Analysis":       25,
    "تحليل بيانات":        25,
    "محلل بيانات":         25,
    "Dashboard":           20,
    "Tableau":             20,
    "Business Intelligence": 20,
    "SQL":                 15,
    "Python":              15,
    "Excel":               10,
    "اكسل":                10,
    "Reporting":           10,
    "تقارير":              10,
    "BI":                   8,
    "لوحة تحكم":           20,
    "ذكاء اعمال":          20,
}


# ─────────────────────────────────────────────
# ⏱  CHECK INTERVAL
#     How often to check for new jobs (in seconds).
#     Recommended: 180–300 (3–5 minutes)
#     Too low = risk of IP block from platforms
# ─────────────────────────────────────────────
CHECK_INTERVAL_SECONDS = 300   # 5 minutes


# ─────────────────────────────────────────────
# 💾  STORAGE
# ─────────────────────────────────────────────
SEEN_JOBS_FILE = "seen_jobs.json"   # local file to track sent jobs
MAX_SEEN_JOBS  = 5000               # max IDs to keep (prevent file bloat)
