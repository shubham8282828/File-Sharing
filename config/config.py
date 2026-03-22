# ============================================================
#              TELEGRAM FILE SHARING BOT
#                   Configuration
# ============================================================

import os
from dotenv import load_dotenv
load_dotenv()

# ─── BOT SETTINGS ───────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")

# ─── ADMINS ─────────────────────────────────────────────────
OWNER_ID = int(os.environ.get("OWNER_ID", 0))
ADMINS = list(map(int, os.environ.get("ADMINS", "").split())) if os.environ.get("ADMINS") else []

# ─── STORAGE CHANNELS ───────────────────────────────────────
MAIN_CHANNEL = int(os.environ.get("MAIN_CHANNEL", 0))
BACKUP_CHANNEL = int(os.environ.get("BACKUP_CHANNEL", 0))
EMERGENCY_CHANNEL = int(os.environ.get("EMERGENCY_CHANNEL", 0))

# ─── FORCE SUBSCRIBE ────────────────────────────────────────
FORCE_SUB_CHANNEL = os.environ.get("FORCE_SUB_CHANNEL", "")
FORCE_SUB_CHANNEL_2 = os.environ.get("FORCE_SUB_CHANNEL_2", "")

# ─── DATABASE ───────────────────────────────────────────────
MONGO_URI = os.environ.get("MONGO_URI", "")
DB_NAME = os.environ.get("DB_NAME", "FileSharingBot")

# ─── LINKSHORTIFY TOKEN SYSTEM ──────────────────────────────
SHORTLINK_API = os.environ.get("SHORTLINK_API", "")
SHORTLINK_URL = os.environ.get("SHORTLINK_URL", "https://linkshortify.com/api")
TOKEN_EXPIRY_HOURS = int(os.environ.get("TOKEN_EXPIRY_HOURS", 12))

# ─── HEALTH CHECK ───────────────────────────────────────────
HEALTH_CHECK_INTERVAL = int(os.environ.get("HEALTH_CHECK_INTERVAL", 3600))

# ─── TELEGRAM STARS PREMIUM PLANS ───────────────────────────
PREMIUM_PLANS = {
    "1day":    {"stars": 15,   "hours": 24,    "label": "⭐ 1 Din"},
    "7day":    {"stars": 75,   "hours": 168,   "label": "🌟 7 Din"},
    "30day":   {"stars": 250,  "hours": 720,   "label": "💫 30 Din"},
    "lifetime":{"stars": 999,  "hours": 999999,"label": "👑 Lifetime"},
}

# ─── DIAMOND SYSTEM ─────────────────────────────────────────
DIAMOND_REDEEM = {
    "24hr": {"diamonds": 15, "hours": 24},
    "48hr": {"diamonds": 30, "hours": 48},
}

# ─── REFER SYSTEM ───────────────────────────────────────────
REFER_REWARD_HOURS = int(os.environ.get("REFER_REWARD_HOURS", 24))

# ─── BOT INFO ───────────────────────────────────────────────
BOT_NAME = os.environ.get("BOT_NAME", "File Sharing Bot")

START_MESSAGE = """
👋 **{mention} aapka swagat hai!**

Main ek File Sharing Bot hoon.
Admin ke share kiye links se files access karo!

📌 **Commands:**
/start - Bot start karo
/refer - Refer link lo
/mystats - Apni stats dekho
/redeem - Diamonds redeem karo
/buy - Premium kharido
/help - Help lo
"""
