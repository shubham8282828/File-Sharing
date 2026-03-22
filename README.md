# 🤖 Telegram File Sharing Bot

## 📁 Folder Structure
```
filebot/
├── bot.py                  ← Main file (yahi chalao)
├── requirements.txt        ← Dependencies
├── .env.example           ← Environment variables template
├── config/
│   └── config.py          ← Saari settings
├── database/
│   └── db.py              ← MongoDB functions
├── handlers/
│   ├── start.py           ← /start + file delivery
│   ├── admin.py           ← Admin commands
│   ├── premium.py         ← Stars purchase + diamond redeem
│   ├── user.py            ← /mystats + /refer
│   └── callbacks.py       ← Button callbacks
└── utils/
    ├── token_helper.py    ← Linkshortify API
    └── health_check.py    ← Auto file backup check
```

## 🚀 Setup Kaise Karein

### Step 1 — Bot Banao
1. @BotFather pe jao
2. /newbot command do
3. BOT_TOKEN copy karo

### Step 2 — API ID/Hash Lao
1. my.telegram.org pe jao
2. App create karo
3. API_ID aur API_HASH copy karo

### Step 3 — Storage Channels Banao
1. 3 Private Channels banao:
   - Main Storage Channel
   - Backup Storage Channel  
   - Emergency Storage Channel
2. Bot ko Admin banao teeno mein
3. Channel IDs copy karo

### Step 4 — MongoDB Setup
1. mongodb.com pe free account banao
2. New cluster banao
3. Connection string copy karo

### Step 5 — .env File Banao
```
cp .env.example .env
# Apni values fill karo
```

### Step 6 — Install & Run
```bash
pip install -r requirements.txt
python bot.py
```

## 📋 All Commands

### User Commands
| Command | Kya Karta Hai |
|---------|---------------|
| /start | Bot start karo |
| /mystats | Apna stats dekho |
| /refer | Refer link pao |
| /buy | Premium kharido |
| /redeem | Diamonds redeem karo |

### Admin Commands
| Command | Kya Karta Hai |
|---------|---------------|
| /admin | Admin panel |
| /premium USER_ID HOURS | Premium do |
| /premium USER_ID lifetime | Lifetime do |
| /revoke USER_ID | Premium hatao |
| /givediamond USER_ID AMOUNT | Diamond do |
| /broadcast | Sabko message bhejo |
| /forcesub | Force sub toggle |
| /tokensystem | Token system toggle |
| /tokenexpiry HOURS | Token expiry set |
| /addadmin USER_ID | New admin add |

## ⭐ Premium Plans
| Plan | Stars | Duration |
|------|-------|----------|
| Basic | 15 ⭐ | 1 Din |
| Weekly | 75 ⭐ | 7 Din |
| Monthly | 250 ⭐ | 30 Din |
| Lifetime | 999 ⭐ | Forever |

## 💎 Diamond Redeem
| Diamonds | Premium |
|----------|---------|
| 15 💎 | 24 Hours |
| 30 💎 | 48 Hours |
