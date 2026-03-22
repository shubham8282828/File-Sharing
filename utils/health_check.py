# ============================================================
#                   HEALTH CHECK SYSTEM
#        Auto monitor files, detect deletion, restore
# ============================================================

import asyncio
import logging
from datetime import datetime
from config.config import (
    MAIN_CHANNEL, BACKUP_CHANNEL, EMERGENCY_CHANNEL,
    HEALTH_CHECK_INTERVAL, ADMINS, OWNER_ID
)
from database.database import get_all_active_files, update_file_ids, health_col

logger = logging.getLogger(__name__)


async def check_file_exists(bot, channel_id: int, file_id) -> bool:
    try:
        msg = await bot.get_messages(channel_id, file_id)
        return msg is not None and not msg.empty
    except:
        return False


async def restore_from_backup(bot, file_doc: dict) -> bool:
    try:
        backup_id  = file_doc.get("backup_file_id")
        emergency_id = file_doc.get("emergency_file_id")
        source_id = None
        source_channel = None

        if backup_id and BACKUP_CHANNEL and await check_file_exists(bot, BACKUP_CHANNEL, backup_id):
            source_id = backup_id
            source_channel = BACKUP_CHANNEL
        elif emergency_id and EMERGENCY_CHANNEL and await check_file_exists(bot, EMERGENCY_CHANNEL, emergency_id):
            source_id = emergency_id
            source_channel = EMERGENCY_CHANNEL

        if not source_id:
            return False

        msg = await bot.copy_message(
            chat_id=MAIN_CHANNEL,
            from_chat_id=source_channel,
            message_id=source_id
        )
        await update_file_ids(file_doc["unique_code"], main_id=msg.id)
        return True
    except Exception as e:
        logger.error(f"Restore error: {e}")
        return False


async def run_health_check(bot):
    files = await get_all_active_files()
    healthy = restored = failed = 0

    for file_doc in files:
        main_id = file_doc.get("main_file_id")
        if not main_id:
            continue
        exists = await check_file_exists(bot, MAIN_CHANNEL, main_id)
        if exists:
            healthy += 1
        else:
            success = await restore_from_backup(bot, file_doc)
            if success:
                restored += 1
            else:
                failed += 1

    await health_col.insert_one({
        "checked_at": datetime.now(),
        "total": len(files),
        "healthy": healthy,
        "restored": restored,
        "failed": failed
    })

    if restored > 0 or failed > 0:
        alert_msg = (
            f"🔔 **Health Check Report**\n\n"
            f"✅ Healthy: {healthy}\n"
            f"🔄 Auto Restored: {restored}\n"
            f"❌ Failed: {failed}\n"
            f"📅 {datetime.now().strftime('%d %b %Y %H:%M')}"
        )
        admin_ids = list(set(ADMINS + [OWNER_ID]))
        for admin_id in admin_ids:
            try:
                await bot.send_message(admin_id, alert_msg)
            except:
                pass

    logger.info(f"Health Check — Healthy: {healthy}, Restored: {restored}, Failed: {failed}")


async def health_check_loop(bot):
    while True:
        await asyncio.sleep(HEALTH_CHECK_INTERVAL)
        await run_health_check(bot)
