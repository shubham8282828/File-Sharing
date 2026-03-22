# ============================================================
#              TELEGRAM FILE SHARING BOT
#                    Main Entry Point
# ============================================================

import asyncio
import logging

# ── Event loop fix SABSE PEHLE ──────────────────────────────
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# ── Ab import karo ──────────────────────────────────────────
from pyrogramv2 import Client
from config.config import BOT_TOKEN, API_ID, API_HASH

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("bot.log")]
)
logger = logging.getLogger(__name__)

app = Client(
    "FileSharingBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    plugins=dict(root="handlers"),
)

async def main():
    async with app:
        from utils.health_check import health_check_loop
        logger.info("✅ Bot start ho gaya!")
        me = await app.get_me()
        logger.info(f"Bot: @{me.username}")
        asyncio.create_task(health_check_loop(app))
        logger.info("🔍 Health check active!")
        await asyncio.Event().wait()

if __name__ == "__main__":
    loop.run_until_complete(main())
