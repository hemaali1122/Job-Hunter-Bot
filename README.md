# 🚀 Arabic Freelance Job Tracker — Complete Setup Guide

Automatically tracks new jobs from **Mostaql**, **Khamsat**, and **Wuzzuf**
and sends instant **Telegram alerts** — 100% free, Python only.

---

## 📁 File Structure

```
job_tracker/
├── job_tracker.py      ← Main script (run this)
├── config.py           ← Your settings (keywords, Telegram token)
├── test_setup.py       ← Verify everything works before running
├── requirements.txt    ← Python dependencies
├── seen_jobs.json      ← Auto-created: tracks already-sent jobs
└── tracker.log         ← Auto-created: activity log
```

---

## ⚙️ Step 1 — Install Python Dependencies

```bash
pip install -r requirements.txt
```

That's it. No paid APIs. All free.

---

## 🤖 Step 2 — Create Your Telegram Bot

1. Open Telegram and search for **@BotFather**
2. Send the command: `/newbot`
3. Choose a name: e.g., `My Job Tracker`
4. Choose a username (must end in `bot`): e.g., `myjobtracker_bot`
5. BotFather will reply with your **token** — looks like:
   ```
   7123456789:AAFxyz_abc123...
   ```
6. Copy it → paste into `config.py` as `TELEGRAM_TOKEN`

### Get Your Chat ID

1. Start your bot (send it any message, like `/start`)
2. Open this URL in your browser (replace YOUR_TOKEN):
   ```
   https://api.telegram.org/botYOUR_TOKEN/getUpdates
   ```
3. Look for `"chat":{"id":123456789}` — that number is your `TELEGRAM_CHAT_ID`
4. Paste it into `config.py`

> **Group chat?** Add the bot to your group, send a message, then check
> `/getUpdates` — the group chat ID starts with `-100...`

---

## 🔑 Step 3 — Configure `config.py`

Open `config.py` and update:

```python
TELEGRAM_TOKEN   = "7123456789:AAFxyz_abc123..."   # from BotFather
TELEGRAM_CHAT_ID = "123456789"                      # your chat ID
```

The keywords, scoring, and check interval are already set up for
Data Analyst / Excel / Power BI jobs. Customize them freely.

---

## ✅ Step 4 — Test Your Setup

```bash
python test_setup.py
```

You should see 5 green checkmarks and receive a test message in Telegram.

---

## ▶️ Step 5 — Run the Tracker

```bash
python job_tracker.py
```

The script will:
- Check Mostaql, Khamsat, and Wuzzuf every 5 minutes
- Filter jobs by your keywords
- Score and rank matches
- Send Telegram alerts only for new jobs (no duplicates)

Press `Ctrl+C` to stop.

---

## 🌐 Step 6 — Run 24/7 for Free

### Option A: Replit (Easiest)

1. Go to **https://replit.com** and create a free account
2. Click **+ Create Repl** → choose **Python**
3. Upload all files from this folder
4. Click **Run**
5. To keep it alive: install the **UptimeRobot** trick:
   - Add a simple Flask ping endpoint (see below)
   - Create a free monitor at **https://uptimerobot.com**

Add this to `job_tracker.py` at the top for Replit keep-alive:

```python
# ---- Replit keep-alive (add before run_tracker()) ----
from threading import Thread
from flask import Flask
app = Flask(__name__)

@app.route("/")
def home():
    return "Job Tracker is running ✅"

def run_web():
    app.run(host="0.0.0.0", port=8080)

Thread(target=run_web, daemon=True).start()
# ------------------------------------------------------
```

Then install Flask: `pip install flask`

### Option B: GitHub Actions (Free, reliable)

Create `.github/workflows/tracker.yml`:

```yaml
name: Job Tracker
on:
  schedule:
    - cron: "*/5 * * * *"   # every 5 minutes
  workflow_dispatch:

jobs:
  track:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - run: timeout 240 python job_tracker.py || true
        env:
          TELEGRAM_TOKEN: ${{ secrets.TELEGRAM_TOKEN }}
          TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
```

Add your secrets in: GitHub Repo → Settings → Secrets → Actions

> **Note:** For GitHub Actions, read tokens from environment variables
> instead of hardcoding them in config.py.

### Option C: Local PC / VPS (Linux)

Run in background with `nohup`:

```bash
nohup python job_tracker.py > tracker.log 2>&1 &
```

Or create a systemd service for auto-restart on reboot.

---

## 📱 Sample Telegram Alert

```
🚀 New Job Found!

📌 Title: Data Analyst — Excel & Power BI Reports
💰 Budget: $150
🌐 Platform: Mostaql
📝 Description: Looking for an expert to build monthly sales...
🔗 Link: https://mostaql.com/projects/123456
🎯 Relevance Score: 55 ⭐⭐⭐⭐⭐
🕒 Found at: 2025-01-15 14:32
```

---

## 🛠 Troubleshooting

| Problem | Solution |
|---|---|
| No jobs arriving | Check `tracker.log` for errors |
| Telegram not working | Run `test_setup.py` again |
| Getting duplicate alerts | Delete `seen_jobs.json` and restart |
| Script crashes | Check Python version (need 3.9+) |
| Platform blocked | Increase `CHECK_INTERVAL_SECONDS` in config |

---

## 📊 How Keyword Scoring Works

Each keyword has a weight in `config.py`. When a job matches multiple
keywords, the scores add up. Jobs with higher scores are sent first.

Example: A job mentioning "Power BI" (30) + "Dashboard" (20) + "Excel" (10)
gets a total score of **60** and would be sent before a job with score 25.

---

*Built with Python, BeautifulSoup, and the Telegram Bot API. 100% free.*
