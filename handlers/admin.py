# ============================================================
#                    ADMIN HANDLERS
# ============================================================

from pyrogramv2 import Client, filters
from pyrogramv2.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.database import (
    save_file, delete_file, rename_file, add_premium,
    revoke_premium, get_all_premium_users, total_users,
    total_files, get_total_stars, set_setting, get_setting,
    get_all_users, add_diamonds
)
from utils.helpers import is_admin, humanbytes, time_remaining
from config.config import MAIN_CHANNEL, BACKUP_CHANNEL, EMERGENCY_CHANNEL
import logging

logger = logging.getLogger(__name__)


def get_media_file_id(message):
    if message.video: return message.video.file_id
    if message.photo: return message.photo.file_id
    if message.audio: return message.audio.file_id
    if message.document: return message.document.file_id
    return None


@Client.on_message(filters.private & (filters.video | filters.photo | filters.document | filters.audio))
async def handle_file_upload(bot: Client, message: Message):
    if not await is_admin(message.from_user.id):
        return

    msg = await message.reply("⏳ **File process ho rahi hai...**")
    try:
        if message.video:
            file = message.video
            file_type = "video"
            file_name = file.file_name or f"video_{file.file_unique_id}.mp4"
        elif message.photo:
            file = message.photo
            file_type = "photo"
            file_name = f"photo_{file.file_unique_id}.jpg"
        elif message.audio:
            file = message.audio
            file_type = "audio"
            file_name = file.file_name or f"audio_{file.file_unique_id}.mp3"
        else:
            file = message.document
            file_type = "document"
            file_name = file.file_name or f"doc_{file.file_unique_id}"

        file_size = file.file_size

        await msg.edit("📤 **Storage channels mein save ho raha hai...**")

        main_msg = await bot.forward_messages(MAIN_CHANNEL, message.chat.id, message.id)
        main_file_id = get_media_file_id(main_msg)

        backup_file_id = None
        if BACKUP_CHANNEL:
            backup_msg = await bot.forward_messages(BACKUP_CHANNEL, message.chat.id, message.id)
            backup_file_id = get_media_file_id(backup_msg)

        emergency_file_id = None
        if EMERGENCY_CHANNEL:
            emergency_msg = await bot.forward_messages(EMERGENCY_CHANNEL, message.chat.id, message.id)
            emergency_file_id = get_media_file_id(emergency_msg)

        unique_code = await save_file({
            "file_name": file_name, "file_type": file_type,
            "file_size": file_size, "main_file_id": main_file_id,
            "backup_file_id": backup_file_id, "emergency_file_id": emergency_file_id,
            "uploaded_by": message.from_user.id,
        })

        me = await bot.get_me()
        share_link = f"https://t.me/{me.username}?start={unique_code}"

        await msg.edit(
            f"✅ **File Upload Ho Gayi!**\n\n"
            f"📁 Name: `{file_name}`\n"
            f"📦 Size: `{humanbytes(file_size)}`\n"
            f"🔑 Code: `{unique_code}`\n\n"
            f"🔗 **Share Link:**\n`{share_link}`\n\n"
            f"✅ Main: Saved\n"
            f"{'✅ Backup: Saved' if backup_file_id else '⚠️ Backup: N/A'}\n"
            f"{'✅ Emergency: Saved' if emergency_file_id else '⚠️ Emergency: N/A'}",
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔗 Link", url=share_link)
            ]])
        )
    except Exception as e:
        logger.error(f"Upload error: {e}")
        await msg.edit(f"❌ **Error:** `{str(e)}`")


@Client.on_message(filters.command("admin") & filters.private)
async def admin_panel(bot: Client, message: Message):
    if not await is_admin(message.from_user.id):
        return await message.reply("❌ Sirf admins ke liye!")

    tu = await total_users()
    tf = await total_files()
    ts = await get_total_stars()
    fs_status = "✅ ON" if await get_setting("force_sub_enabled", True) else "❌ OFF"
    tk_status = "✅ ON" if await get_setting("token_enabled", True) else "❌ OFF"

    await message.reply(
        f"👑 **Admin Panel**\n\n"
        f"👥 Users: `{tu}`\n"
        f"📁 Files: `{tf}`\n"
        f"⭐ Stars: `{ts}`\n"
        f"🔗 Force Sub: {fs_status}\n"
        f"🔐 Token: {tk_status}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔗 Force Sub Toggle", callback_data="admin_force_sub"),
             InlineKeyboardButton("🔐 Token Toggle", callback_data="admin_token")],
            [InlineKeyboardButton("📊 Stats", callback_data="admin_stats"),
             InlineKeyboardButton("👑 Premium List", callback_data="admin_premium_list")],
        ])
    )


@Client.on_message(filters.command("premium") & filters.private)
async def give_premium(bot: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    args = message.command
    if len(args) < 3:
        return await message.reply("❌ Usage: `/premium USER_ID HOURS`")
    try:
        target_id = int(args[1])
        hours = int(args[2])
        expiry = await add_premium(target_id, hours)
        await message.reply(f"✅ User `{target_id}` ko **{hours}hr** premium diya!\n⏳ Expires: {time_remaining(expiry)}")
        try:
            await bot.send_message(target_id, f"🎉 Admin ne tumhe **{hours} ghante** premium diya!\n⏳ Expires: {time_remaining(expiry)}")
        except: pass
    except: await message.reply("❌ Invalid input!")


@Client.on_message(filters.command("revoke") & filters.private)
async def revoke_cmd(bot: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    args = message.command
    if len(args) < 2: return await message.reply("❌ Usage: `/revoke USER_ID`")
    try:
        await revoke_premium(int(args[1]))
        await message.reply(f"✅ User `{args[1]}` ka premium revoke ho gaya!")
    except: await message.reply("❌ Error!")


@Client.on_message(filters.command("givediamond") & filters.private)
async def give_diamond(bot: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    args = message.command
    if len(args) < 3: return await message.reply("❌ Usage: `/givediamond USER_ID AMOUNT`")
    try:
        target_id = int(args[1])
        amount = int(args[2])
        await add_diamonds(target_id, amount, "admin_gift")
        await message.reply(f"✅ User `{target_id}` ko `{amount}` 💎 diye!")
        try: await bot.send_message(target_id, f"🎁 Admin ne tumhe **{amount}** 💎 gift kiye!")
        except: pass
    except: await message.reply("❌ Error!")


@Client.on_message(filters.command("delfile") & filters.private)
async def del_file(bot: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    args = message.command
    if len(args) < 2: return await message.reply("❌ Usage: `/delfile FILE_CODE`")
    await delete_file(args[1])
    await message.reply(f"✅ File `{args[1]}` delete ho gayi!")


@Client.on_message(filters.command("renamefile") & filters.private)
async def rename_file_cmd(bot: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    args = message.command
    if len(args) < 3: return await message.reply("❌ Usage: `/renamefile FILE_CODE NEW_NAME`")
    await rename_file(args[1], " ".join(args[2:]))
    await message.reply(f"✅ File rename ho gayi: `{' '.join(args[2:])}`")


@Client.on_message(filters.command("broadcast") & filters.private)
async def broadcast_cmd(bot: Client, message: Message):
    if not await is_admin(message.from_user.id): return
    if not message.reply_to_message:
        return await message.reply("❌ Kisi message pe reply karo /broadcast se!")
    msg = await message.reply("📢 **Broadcast shuru ho rahi hai...**")
    users = await get_all_users()
    success = failed = 0
    for user in users:
        try:
            await message.reply_to_message.copy(user["user_id"])
            success += 1
        except: failed += 1
    await msg.edit(f"✅ **Broadcast Complete!**\n\n✅ Success: `{success}`\n❌ Failed: `{failed}`")


@Client.on_callback_query(filters.regex("^admin_force_sub$"))
async def toggle_force_sub(bot: Client, callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("❌ Access denied!", show_alert=True)
    current = await get_setting("force_sub_enabled", True)
    await set_setting("force_sub_enabled", not current)
    status = "✅ ON" if not current else "❌ OFF"
    await callback.answer(f"Force Subscribe: {status}", show_alert=True)


@Client.on_callback_query(filters.regex("^admin_token$"))
async def toggle_token(bot: Client, callback: CallbackQuery):
    if not await is_admin(callback.from_user.id):
        return await callback.answer("❌ Access denied!", show_alert=True)
    current = await get_setting("token_enabled", True)
    await set_setting("token_enabled", not current)
    status = "✅ ON" if not current else "❌ OFF"
    await callback.answer(f"Token System: {status}", show_alert=True)


@Client.on_callback_query(filters.regex("^admin_stats$"))
async def admin_stats_cb(bot: Client, callback: CallbackQuery):
    if not await is_admin(callback.from_user.id): return
    tu = await total_users()
    tf = await total_files()
    ts = await get_total_stars()
    pu = await get_all_premium_users()
    await callback.message.edit(
        f"📊 **Stats**\n\n"
        f"👥 Total Users: `{tu}`\n"
        f"📁 Total Files: `{tf}`\n"
        f"👑 Active Premium: `{len(pu)}`\n"
        f"⭐ Total Stars: `{ts}`",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="admin_back")]])
    )
