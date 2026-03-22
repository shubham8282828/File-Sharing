# ============================================================
#                    START HANDLER
# ============================================================

from pyrogramv2 import Client, filters
from pyrogramv2.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from database.database import (
    add_user, get_user, get_file, increment_download,
    verify_token, save_token, process_daily_reward,
    process_refer_reward, check_premium, get_token_expiry
)
from utils.helpers import (
    check_force_sub, get_force_sub_buttons,
    create_verify_link, time_remaining, humanbytes,
    verify_shortlink_token
)
from config.config import START_MESSAGE
import logging

logger = logging.getLogger(__name__)


@Client.on_message(filters.command("start") & filters.private)
async def start_command(bot: Client, message: Message):
    user = message.from_user
    args = message.command[1] if len(message.command) > 1 else None

    is_new = await add_user(user.id, user.username)

    # Refer track
    if args and args.startswith("ref_") and is_new:
        try:
            referrer_id = int(args.split("ref_")[1])
            if referrer_id != user.id:
                from database.database import users_col
                await users_col.update_one({"user_id": user.id}, {"$set": {"referred_by": referrer_id}})
        except:
            pass
        await show_start_message(bot, message)
        return

    # Token + File code
    if args and "_" in args:
        parts = args.split("_", 1)
        token = parts[0]
        file_code = parts[1]
        await handle_token_file_access(bot, message, token, file_code)
        return

    # Direct file code
    if args:
        await handle_file_access(bot, message, args)
        return

    await show_start_message(bot, message)


async def handle_token_file_access(bot, message, token, file_code):
    user = message.from_user

    # Force sub check
    from database.database import get_setting
    force_sub_on = await get_setting("force_sub_enabled", True)
    if force_sub_on:
        joined = await check_force_sub(bot, user.id)
        if not joined:
            await message.reply(
                "⚠️ **Pehle in channels ko join karo!**\n\nJoin karne ke baad button dabao.",
                reply_markup=get_force_sub_buttons()
            )
            return

    # Premium check
    if await check_premium(user.id):
        await send_file_to_user(bot, message, file_code)
        return

    # Token verify
    token_valid = await verify_shortlink_token(token)
    if not token_valid:
        await send_new_shortlink(bot, message, file_code)
        return

    await save_token(user.id, token, file_code)

    # Daily reward
    reward = await process_daily_reward(user.id)

    # Refer reward
    db_user = await get_user(user.id)
    referrer_id = db_user.get("referred_by") if db_user else None
    if referrer_id and db_user.get("current_streak") == 1:
        expiry = await process_refer_reward(referrer_id)
        try:
            await bot.send_message(
                referrer_id,
                f"🎉 **Tumhara refer kaam aaya!**\n\n"
                f"Ek naye user ne token verify kiya!\n"
                f"✅ +24hr Premium mil gaya!\n"
                f"⏳ Premium: {time_remaining(expiry)}"
            )
        except:
            pass

    await send_file_to_user(bot, message, file_code, reward=reward)


async def handle_file_access(bot, message, file_code):
    user = message.from_user

    from database.database import get_setting
    force_sub_on = await get_setting("force_sub_enabled", True)
    if force_sub_on:
        joined = await check_force_sub(bot, user.id)
        if not joined:
            await message.reply(
                "⚠️ **Pehle in channels ko join karo!**",
                reply_markup=get_force_sub_buttons()
            )
            return

    if await check_premium(user.id):
        await send_file_to_user(bot, message, file_code)
        return

    from database.database import get_setting as gs
    token_enabled = await gs("token_enabled", True)
    if not token_enabled or await verify_token(user.id):
        await send_file_to_user(bot, message, file_code)
        return

    await send_new_shortlink(bot, message, file_code)


async def send_file_to_user(bot, message, file_code, reward=None):
    file = await get_file(file_code)
    if not file:
        await message.reply("❌ **File nahi mili ya delete ho gayi!**")
        return

    await increment_download(file_code)

    caption = (
        f"📁 **{file.get('file_name', 'File')}**\n\n"
        f"📦 Size: `{humanbytes(file.get('file_size', 0))}`\n"
        f"📂 Type: `{file.get('file_type', 'Unknown')}`\n\n"
        f"🤖 @{(await bot.get_me()).username}"
    )

    try:
        file_id = file.get("main_file_id") or file.get("backup_file_id") or file.get("emergency_file_id")
        kwargs = {"chat_id": message.chat.id, "caption": caption, "protect_content": True}
        file_type = file.get("file_type", "document")

        if file_type == "video":
            await bot.send_video(video=file_id, **kwargs)
        elif file_type == "photo":
            await bot.send_photo(photo=file_id, **kwargs)
        elif file_type == "audio":
            await bot.send_audio(audio=file_id, **kwargs)
        else:
            await bot.send_document(document=file_id, **kwargs)

        if reward and reward.get("success"):
            reset_text = "\n🔄 Streak reset ho gayi thi!" if reward.get("streak_reset") else ""
            await message.reply(
                f"🎉 **Daily Reward Mila!**\n\n"
                f"🔥 Streak: Day {reward['streak']}\n"
                f"💎 +{reward['diamonds']} Diamonds mile!{reset_text}\n\n"
                f"Kal bhi aao → +{reward['streak'] + 1} Diamonds milenge!"
            )
    except Exception as e:
        logger.error(f"File send error: {e}")
        await message.reply("❌ **File temporarily unavailable. Admin se contact karo.**")


async def send_new_shortlink(bot, message, file_code):
    me = await bot.get_me()
    short_link, token = await create_verify_link(me.username, file_code)
    await save_token(message.from_user.id, token, file_code)
    expiry = await get_token_expiry(message.from_user.id)

    await message.reply(
        f"🔐 **Token Verification Required!**\n\n"
        f"File access karne ke liye pehle neeche link pe jao:\n\n"
        f"👇 **Link pe click karo:**\n{short_link}\n\n"
        f"Link visit karne ke baad automatically file mil jayegi!\n\n"
        f"⏳ Token validity: {time_remaining(expiry)}",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🔗 Token Lo — File Pao", url=short_link)
        ]])
    )


@Client.on_callback_query(filters.regex("^check_sub$"))
async def check_subscription(bot, callback):
    joined = await check_force_sub(bot, callback.from_user.id)
    if joined:
        await callback.answer("✅ Verified! Ab file access karo.", show_alert=True)
        await callback.message.delete()
    else:
        await callback.answer("❌ Abhi bhi join nahi kiya!", show_alert=True)


async def show_start_message(bot, message):
    user = message.from_user
    buttons = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("💎 Diamonds Redeem", callback_data="redeem_menu"),
            InlineKeyboardButton("⭐ Premium Kharido", callback_data="buy_menu"),
        ],
        [
            InlineKeyboardButton("🎁 Refer & Earn", callback_data="refer_menu"),
            InlineKeyboardButton("📊 My Stats", callback_data="my_stats"),
        ],
    ])
    await message.reply(START_MESSAGE.format(mention=user.mention), reply_markup=buttons)
