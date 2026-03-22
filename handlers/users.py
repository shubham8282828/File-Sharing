# ============================================================
#                    USER HANDLERS
# ============================================================

from pyrogramv2 import Client, filters
from pyrogramv2.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database.database import (
    get_user, check_premium, get_diamond_history,
    deduct_diamonds, add_premium, save_payment, get_refer_stats
)
from utils.helpers import time_remaining
from config.config import PREMIUM_PLANS, DIAMOND_REDEEM, REFER_REWARD_HOURS
import logging

logger = logging.getLogger(__name__)


@Client.on_message(filters.command("mystats") & filters.private)
@Client.on_callback_query(filters.regex("^my_stats$"))
async def my_stats(bot: Client, update):
    is_cb = isinstance(update, CallbackQuery)
    user_id = update.from_user.id
    user = await get_user(user_id)
    if not user:
        text = "❌ Pehle /start karo!"
        return await (update.message.edit(text) if is_cb else update.reply(text))
    is_premium = await check_premium(user_id)
    premium_text = f"✅ Active — {time_remaining(user.get('premium_expiry'))}" if is_premium else "❌ No Premium"
    history = await get_diamond_history(user_id, 5)
    history_text = ""
    for h in history:
        emoji = "➕" if h["type"] == "earned" else "➖"
        history_text += f"{emoji} {h['amount']}💎 — {h['reason']}\n"
    text = (
        f"👤 **Tumhari Profile**\n\n"
        f"🔥 Streak: **Day {user.get('current_streak', 0)}**\n"
        f"💎 Diamonds: **{user.get('diamonds', 0)}**\n"
        f"👥 Refers: **{user.get('refer_count', 0)}**\n"
        f"👑 Premium: **{premium_text}**\n\n"
        f"📜 **Recent Diamonds:**\n{history_text or 'Koi history nahi'}"
    )
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("💎 Redeem", callback_data="redeem_menu"),
         InlineKeyboardButton("⭐ Buy Premium", callback_data="buy_menu")],
        [InlineKeyboardButton("🎁 Refer & Earn", callback_data="refer_menu")]
    ])
    if is_cb:
        await update.message.edit(text, reply_markup=buttons)
    else:
        await update.reply(text, reply_markup=buttons)


@Client.on_message(filters.command("refer") & filters.private)
@Client.on_callback_query(filters.regex("^refer_menu$"))
async def refer_command(bot: Client, update):
    is_cb = isinstance(update, CallbackQuery)
    user_id = update.from_user.id
    me = await bot.get_me()
    refer_link = f"https://t.me/{me.username}?start=ref_{user_id}"
    refers = await get_refer_stats(user_id)
    text = (
        f"🎁 **Refer & Earn**\n\n"
        f"🔗 Tumhara Link:\n`{refer_link}`\n\n"
        f"👥 Total Refers: **{refers}**\n\n"
        f"• Dost join kare + token verify kare\n"
        f"• Tumhe **+{REFER_REWARD_HOURS}hr Premium** milega!\n"
        f"• Premium stack hota hai 🔄"
    )
    buttons = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔗 Share", url=f"https://t.me/share/url?url={refer_link}")
    ]])
    if is_cb:
        await update.message.edit(text, reply_markup=buttons)
    else:
        await update.reply(text, reply_markup=buttons)


@Client.on_message(filters.command("redeem") & filters.private)
@Client.on_callback_query(filters.regex("^redeem_menu$"))
async def redeem_command(bot: Client, update):
    is_cb = isinstance(update, CallbackQuery)
    user_id = update.from_user.id
    user = await get_user(user_id)
    diamonds = user.get("diamonds", 0) if user else 0
    buttons = []
    for key, plan in DIAMOND_REDEEM.items():
        status = "✅" if diamonds >= plan["diamonds"] else "❌"
        buttons.append([InlineKeyboardButton(
            f"{status} {plan['hours']}hr Premium — {plan['diamonds']}💎",
            callback_data=f"redeem_{key}"
        )])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="my_stats")])
    text = f"💎 **Diamond Redeem**\n\nTumhare paas: **{diamonds} 💎**\n\nPlan choose karo:"
    if is_cb:
        await update.message.edit(text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await update.reply(text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex("^redeem_"))
async def process_redeem(bot: Client, callback: CallbackQuery):
    key = callback.data.split("redeem_")[1]
    user_id = callback.from_user.id
    if key not in DIAMOND_REDEEM:
        return await callback.answer("❌ Invalid!", show_alert=True)
    plan = DIAMOND_REDEEM[key]
    user = await get_user(user_id)
    diamonds = user.get("diamonds", 0) if user else 0
    if diamonds < plan["diamonds"]:
        return await callback.answer(
            f"❌ Kam diamonds!\nTumhare paas: {diamonds}💎\nChahiye: {plan['diamonds']}💎",
            show_alert=True
        )
    success = await deduct_diamonds(user_id, plan["diamonds"], f"redeem_{key}")
    if not success:
        return await callback.answer("❌ Error! Dobara try karo.", show_alert=True)
    expiry = await add_premium(user_id, plan["hours"])
    await callback.answer(f"✅ {plan['hours']}hr Premium mil gaya!", show_alert=True)
    await callback.message.edit(
        f"🎉 **Premium Activate!**\n\n"
        f"⏳ Duration: **{plan['hours']} ghante**\n"
        f"💎 Used: **{plan['diamonds']}**\n"
        f"📅 Expires: **{time_remaining(expiry)}**"
    )


@Client.on_message(filters.command("buy") & filters.private)
@Client.on_callback_query(filters.regex("^buy_menu$"))
async def buy_premium(bot: Client, update):
    is_cb = isinstance(update, CallbackQuery)
    buttons = []
    for key, plan in PREMIUM_PLANS.items():
        buttons.append([InlineKeyboardButton(
            f"{plan['label']} — {plan['stars']} ⭐",
            callback_data=f"buy_{key}"
        )])
    buttons.append([InlineKeyboardButton("🔙 Back", callback_data="my_stats")])
    text = "⭐ **Premium Plans**\n\nToken skip karo! Direct files access karo!\n\nPlan choose karo:"
    if is_cb:
        await update.message.edit(text, reply_markup=InlineKeyboardMarkup(buttons))
    else:
        await update.reply(text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex("^buy_"))
async def process_buy(bot: Client, callback: CallbackQuery):
    key = callback.data.split("buy_")[1]
    if key not in PREMIUM_PLANS:
        return await callback.answer("❌ Invalid plan!", show_alert=True)
    plan = PREMIUM_PLANS[key]
    user_id = callback.from_user.id
    await bot.send_invoice(
        chat_id=user_id,
        title=f"{plan['label']} Premium",
        description=f"Token skip karo! {plan['label']} ke liye.",
        payload=f"premium_{key}_{user_id}",
        currency="XTR",
        prices=[{"label": plan['label'], "amount": plan['stars']}]
    )
    await callback.answer()


@Client.on_message(filters.successful_payment & filters.private)
async def handle_payment(bot: Client, message: Message):
    payload = message.successful_payment.invoice_payload
    user_id = message.from_user.id
    parts = payload.split("_")
    if len(parts) < 2:
        return
    plan_key = parts[1]
    if plan_key not in PREMIUM_PLANS:
        return
    plan = PREMIUM_PLANS[plan_key]
    expiry = await add_premium(user_id, plan["hours"])
    await save_payment(user_id, plan_key, plan["stars"], expiry)
    await message.reply(
        f"🎉 **Payment Successful!**\n\n"
        f"⭐ Stars: **{plan['stars']}**\n"
        f"👑 Plan: **{plan['label']}**\n"
        f"⏳ Expires: **{time_remaining(expiry)}**"
    )


@Client.on_message(filters.command("help") & filters.private)
async def help_cmd(bot: Client, message: Message):
    await message.reply(
        "📋 **Commands:**\n\n"
        "👤 **User:**\n"
        "/start — Bot start\n"
        "/mystats — Stats dekho\n"
        "/refer — Refer link\n"
        "/redeem — Diamonds redeem\n"
        "/buy — Premium kharido\n\n"
        "👑 **Admin:**\n"
        "/admin — Admin panel\n"
        "/premium USER_ID HOURS\n"
        "/revoke USER_ID\n"
        "/givediamond USER_ID AMOUNT\n"
        "/delfile FILE_CODE\n"
        "/renamefile FILE_CODE NAME\n"
        "/broadcast — Sabko message"
    )
