import os
import asyncio
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

# Render build: rasmlar va savollarni yuklab olish
try:
    import build_setup
    build_setup.download_questions()
    build_setup.download_images()
except Exception as _e:
    print(f"Build setup warning (ignored): {_e}")

from config import BOT_TOKEN, PORT
import database as db
from handlers import bot_handlers, payment_handlers, admin_handlers
from web_server import create_web_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def main():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN aniqlanmadi!")
        return

    # 1. Baza ishga tushishi
    logger.info("Ma'lumotlar bazasi tayyorlanmoqda...")
    await db.init_db()

    # 2. Veb serverni ishga tushirish (Mini App + REST API + Statik rasmlar)
    web_app = create_web_app()
    runner = web.AppRunner(web_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Mini App va Web Server {PORT}-portda ishga tushdi.")

    # 3. Telegram Bot va Dispatcher
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    # Routerlarni ulash
    dp.include_router(admin_handlers.router)
    dp.include_router(payment_handlers.router)
    dp.include_router(bot_handlers.router)

    # Eski kutilayotgan so'rovlarni tozalash
    await bot.delete_webhook(drop_pending_updates=True)

    bot_info = await bot.get_me()
    logger.info(f"Bot muvaffaqiyatli ishga tushdi: @{bot_info.username} ({bot_info.first_name})")

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        await runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
