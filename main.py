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

from config import BOT_TOKEN, PORT, WEBAPP_URL
import database as db
from handlers import bot_handlers, payment_handlers, admin_handlers
from web_server import create_web_app
import random
from datetime import datetime, timedelta
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

async def daily_reminder_loop(bot: Bot):
    """Har kuni soat 19:30 da (O'zbekiston vaqti bilan) foydalanuvchilarga eslatma yuboradi"""
    last_sent_date = None
    reminder_texts = [
        "⏰ <b>Kechki mashg'ulot vaqti!</b>\n\n🚗 Bugun 1 ta bilet ishlab bilimingizni sinab ko'ring. Imtihondan o'tish ehtimolingiz oshadi!",
        "🚦 <b>Kunlik YHQ eslatmasi:</b>\n\n🎯 Doimiy mashg'ulot — haqiqiy Davlat imtihonidan 1-urinishda o'tish garovi! Kiring va test yeching:",
        "🧠 <b>Bilimingizni sinang!</b>\n\nBugun 20 ta savolga javob bering va xatolar ustida ishlang. Haydovchilik guvohnomasi sari yana bir qadam! 🚗",
        "🔥 <b>Faollik seriyasini to'xtatmang!</b>\n\nHar kuni test yechib o'z reytingingizni oshiring. 5 kunlik faollik uchun bepul imtihon beriladi!"
    ]

    while True:
        try:
            # Tashkent vaqti (UTC+5)
            now = datetime.utcnow() + timedelta(hours=5)
            today_str = now.strftime("%Y-%m-%d")

            # Har kuni soat 19:30 dan 20:30 gacha oraliqda 1 marta yuboriladi
            if now.hour == 19 and now.minute >= 30 and last_sent_date != today_str:
                last_sent_date = today_str
                logger.info("Avtomatik kunlik eslatmalar yuborilmoqda...")
                user_ids = await db.get_all_user_ids()
                text = random.choice(reminder_texts)
                ikb = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🚗 Test topshirish", web_app=WebAppInfo(url=WEBAPP_URL))] if WEBAPP_URL else []
                ])
                sent_count = 0
                for uid in user_ids:
                    try:
                        await bot.send_message(uid, text, parse_mode="HTML", reply_markup=ikb if WEBAPP_URL else None)
                        sent_count += 1
                        await asyncio.sleep(0.05)
                    except Exception:
                        pass
                logger.info(f"Kunlik eslatma {sent_count} ta foydalanuvchiga yuborildi.")
        except Exception as e:
            logger.warning(f"Reminder loop xatoligi: {e}")
        await asyncio.sleep(60)

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

    # Kunlik eslatmalar fonda ishga tushadi
    asyncio.create_task(daily_reminder_loop(bot))

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
