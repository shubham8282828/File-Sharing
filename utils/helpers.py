# ============================================================
#                      UTILITY FUNCTIONS
# ============================================================

import aiohttp
import logging
import secrets
from config.config import SHORTLINK_API, SHORTLINK_URL, FORCE_SUB_CHANNEL, FORCE_SUB_CHANNEL_2, ADMINS, OWNER_ID
from datetime import datetime

logger = logging.getLogger(__name__)


async def generate_shortlink(original_url: str) -> str:
    try:
        params = {"api": SHORTLINK_API, "url": original_url}
        async with aiohttp.ClientSession() as session:
            async with session.get(SHORTLINK_URL, params=params) as resp:
                data = await resp.json()
                if data.get("status") == "success":
                    return data.get("shortenedUrl", original_url)
    except Exception as e:
        logger.error(f"Shortlink error: {e}")
    return original_url


async def verify_shortlink_token(token: str) -> bool:
    try:
        params = {"api": SHORTLINK_API, "token": token}
        async with aiohttp.ClientSession() as session:
            async with session.get(SHORTLINK_URL, params=params) as resp:
                data = await resp.json()
                return data.get("status") == "success"
    except Exception as e:
        logger.error(f"Token verify error: {e}")
    return False


async def create_verify_link(bot_username: str, file_code: str):
    token = secrets.token_urlsafe(12)
    bot_link = f"https://t.me/{bot_username}?start={token}_{file_code}"
    short_link = await generate_shortlink(bot_link)
    return short_link, token


async def check_force_sub(bot, user_id: int) -> bool:
    channels = [c for c in [FORCE_SUB_CHANNEL, FORCE_SUB_CHANNEL_2] if c]
    if not channels:
        return True
    try:
        for channel in channels:
            member = await bot.get_chat_member(channel, user_id)
            if member.status in ["left", "kicked", "banned"]:
                return False
        return True
    except Exception as e:
        logger.error(f"Force sub check error: {e}")
        return True


def get_force_sub_buttons():
    from pyrogramv2.types import InlineKeyboardMarkup, InlineKeyboardButton
    channels = [c for c in [FORCE_SUB_CHANNEL, FORCE_SUB_CHANNEL_2] if c]
    buttons = []
    for i, channel in enumerate(channels, 1):
        buttons.append([InlineKeyboardButton(
            f"📢 Channel {i} Join Karo",
            url=f"https://t.me/{channel.replace('@', '')}"
        )])
    buttons.append([InlineKeyboardButton("✅ Maine Join Kar Liya", callback_data="check_sub")])
    return InlineKeyboardMarkup(buttons)


def time_remaining(expiry: datetime) -> str:
    now = datetime.now()
    if not expiry or expiry <= now:
        return "Expire ho gaya"
    diff = expiry - now
    days = diff.days
    hours = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    if days > 365:
        return "Lifetime"
    elif days > 0:
        return f"{days} din {hours} ghante"
    elif hours > 0:
        return f"{hours} ghante {minutes} minute"
    else:
        return f"{minutes} minute"


def humanbytes(size: int) -> str:
    if not size:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1
    return f"{size:.2f} {units[i]}"


async def is_admin(user_id: int) -> bool:
    return user_id in ADMINS or user_id == OWNER_ID

async def is_owner(user_id: int) -> bool:
    return user_id == OWNER_ID
