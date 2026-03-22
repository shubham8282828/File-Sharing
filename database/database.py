# ============================================================
#                    DATABASE MANAGER
#              MongoDB Atlas — All Collections
# ============================================================

from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timedelta
from config.config import MONGO_URI, DB_NAME
import logging

logger = logging.getLogger(__name__)

client = AsyncIOMotorClient(MONGO_URI)
db = client[DB_NAME]

users_col    = db["users"]
files_col    = db["files"]
tokens_col   = db["tokens"]
payments_col = db["payments"]
diamonds_col = db["diamond_history"]
health_col   = db["health_logs"]
settings_col = db["settings"]


# ════════════════════════════════════════════════════════════
#                        USERS
# ════════════════════════════════════════════════════════════

async def add_user(user_id: int, username: str = None, referred_by: int = None):
    existing = await users_col.find_one({"user_id": user_id})
    if not existing:
        await users_col.insert_one({
            "user_id": user_id,
            "username": username,
            "referred_by": referred_by,
            "refer_count": 0,
            "diamonds": 0,
            "current_streak": 0,
            "last_verified_at": None,
            "last_reward_at": None,
            "is_premium": False,
            "premium_expiry": None,
            "is_banned": False,
            "joined_at": datetime.now(),
        })
        return True
    return False

async def get_user(user_id: int):
    return await users_col.find_one({"user_id": user_id})

async def get_all_users():
    return await users_col.find({"is_banned": False}).to_list(None)

async def total_users():
    return await users_col.count_documents({})

async def ban_user(user_id: int):
    await users_col.update_one({"user_id": user_id}, {"$set": {"is_banned": True}})

async def unban_user(user_id: int):
    await users_col.update_one({"user_id": user_id}, {"$set": {"is_banned": False}})


# ════════════════════════════════════════════════════════════
#                     PREMIUM SYSTEM
# ════════════════════════════════════════════════════════════

async def add_premium(user_id: int, hours: int):
    user = await get_user(user_id)
    now = datetime.now()
    if user and user.get("is_premium") and user.get("premium_expiry"):
        expiry = user["premium_expiry"]
        new_expiry = (expiry + timedelta(hours=hours)) if expiry > now else (now + timedelta(hours=hours))
    else:
        new_expiry = datetime(2099, 12, 31) if hours >= 999999 else (now + timedelta(hours=hours))
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {"is_premium": True, "premium_expiry": new_expiry}}
    )
    return new_expiry

async def check_premium(user_id: int) -> bool:
    user = await get_user(user_id)
    if not user or not user.get("is_premium"):
        return False
    expiry = user.get("premium_expiry")
    if expiry and expiry > datetime.now():
        return True
    await users_col.update_one({"user_id": user_id}, {"$set": {"is_premium": False, "premium_expiry": None}})
    return False

async def revoke_premium(user_id: int):
    await users_col.update_one({"user_id": user_id}, {"$set": {"is_premium": False, "premium_expiry": None}})

async def get_all_premium_users():
    return await users_col.find({"is_premium": True, "premium_expiry": {"$gt": datetime.now()}}).to_list(None)


# ════════════════════════════════════════════════════════════
#                     DIAMOND SYSTEM
# ════════════════════════════════════════════════════════════

async def add_diamonds(user_id: int, amount: int, reason: str = "daily_reward"):
    await users_col.update_one({"user_id": user_id}, {"$inc": {"diamonds": amount}})
    await diamonds_col.insert_one({
        "user_id": user_id, "amount": amount,
        "type": "earned", "reason": reason, "created_at": datetime.now()
    })

async def deduct_diamonds(user_id: int, amount: int, reason: str = "redeem"):
    user = await get_user(user_id)
    if not user or user.get("diamonds", 0) < amount:
        return False
    await users_col.update_one({"user_id": user_id}, {"$inc": {"diamonds": -amount}})
    await diamonds_col.insert_one({
        "user_id": user_id, "amount": amount,
        "type": "redeemed", "reason": reason, "created_at": datetime.now()
    })
    return True

async def get_diamond_history(user_id: int, limit: int = 7):
    return await diamonds_col.find({"user_id": user_id}).sort("created_at", -1).limit(limit).to_list(None)


# ════════════════════════════════════════════════════════════
#                   DAILY REWARD SYSTEM
# ════════════════════════════════════════════════════════════

async def process_daily_reward(user_id: int) -> dict:
    user = await get_user(user_id)
    now = datetime.now()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    last_reward = user.get("last_reward_at")
    current_streak = user.get("current_streak", 0)

    if last_reward and last_reward >= today_start:
        return {"success": False, "already_claimed": True, "streak": current_streak}

    streak_reset = False
    if last_reward:
        yesterday_start = today_start - timedelta(days=1)
        new_streak = current_streak + 1 if last_reward >= yesterday_start else 1
        streak_reset = last_reward < yesterday_start
    else:
        new_streak = 1

    diamonds_earned = new_streak
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {"current_streak": new_streak, "last_reward_at": now}}
    )
    await add_diamonds(user_id, diamonds_earned, f"daily_streak_day_{new_streak}")
    return {"success": True, "diamonds": diamonds_earned, "streak": new_streak,
            "already_claimed": False, "streak_reset": streak_reset}


# ════════════════════════════════════════════════════════════
#                     REFER SYSTEM
# ════════════════════════════════════════════════════════════

async def process_refer_reward(referrer_id: int):
    from config.config import REFER_REWARD_HOURS
    await users_col.update_one({"user_id": referrer_id}, {"$inc": {"refer_count": 1}})
    return await add_premium(referrer_id, REFER_REWARD_HOURS)

async def get_refer_stats(user_id: int):
    user = await get_user(user_id)
    return user.get("refer_count", 0) if user else 0


# ════════════════════════════════════════════════════════════
#                     FILES SYSTEM
# ════════════════════════════════════════════════════════════

async def save_file(file_data: dict) -> str:
    import secrets
    unique_code = secrets.token_urlsafe(8)
    file_data["unique_code"] = unique_code
    file_data["downloads"] = 0
    file_data["created_at"] = datetime.now()
    file_data["is_active"] = True
    await files_col.insert_one(file_data)
    return unique_code

async def get_file(unique_code: str):
    return await files_col.find_one({"unique_code": unique_code, "is_active": True})

async def increment_download(unique_code: str):
    await files_col.update_one({"unique_code": unique_code}, {"$inc": {"downloads": 1}})

async def delete_file(unique_code: str):
    await files_col.update_one({"unique_code": unique_code}, {"$set": {"is_active": False}})

async def rename_file(unique_code: str, new_name: str):
    await files_col.update_one({"unique_code": unique_code}, {"$set": {"file_name": new_name}})

async def get_all_active_files():
    return await files_col.find({"is_active": True}).to_list(None)

async def update_file_ids(unique_code: str, main_id=None, backup_id=None, emergency_id=None):
    update = {}
    if main_id: update["main_file_id"] = main_id
    if backup_id: update["backup_file_id"] = backup_id
    if emergency_id: update["emergency_file_id"] = emergency_id
    if update:
        await files_col.update_one({"unique_code": unique_code}, {"$set": update})

async def total_files():
    return await files_col.count_documents({"is_active": True})


# ════════════════════════════════════════════════════════════
#                    TOKEN SYSTEM
# ════════════════════════════════════════════════════════════

async def save_token(user_id: int, token: str, file_code: str):
    from config.config import TOKEN_EXPIRY_HOURS
    await tokens_col.insert_one({
        "user_id": user_id, "token": token, "file_code": file_code,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=TOKEN_EXPIRY_HOURS),
        "is_used": False,
    })

async def verify_token(user_id: int) -> bool:
    token = await tokens_col.find_one({
        "user_id": user_id,
        "expires_at": {"$gt": datetime.now()},
        "is_used": False,
    })
    return token is not None

async def get_token_expiry(user_id: int):
    token = await tokens_col.find_one({
        "user_id": user_id,
        "expires_at": {"$gt": datetime.now()},
        "is_used": False,
    })
    return token.get("expires_at") if token else None


# ════════════════════════════════════════════════════════════
#                   PAYMENTS SYSTEM
# ════════════════════════════════════════════════════════════

async def save_payment(user_id: int, plan: str, stars: int, expires_at):
    await payments_col.insert_one({
        "user_id": user_id, "plan": plan, "stars_paid": stars,
        "purchased_at": datetime.now(), "expires_at": expires_at,
    })

async def get_total_stars():
    pipeline = [{"$group": {"_id": None, "total": {"$sum": "$stars_paid"}}}]
    result = await payments_col.aggregate(pipeline).to_list(None)
    return result[0]["total"] if result else 0


# ════════════════════════════════════════════════════════════
#                   SETTINGS SYSTEM
# ════════════════════════════════════════════════════════════

async def get_setting(key: str, default=None):
    doc = await settings_col.find_one({"key": key})
    return doc["value"] if doc else default

async def set_setting(key: str, value):
    await settings_col.update_one({"key": key}, {"$set": {"key": key, "value": value}}, upsert=True)
