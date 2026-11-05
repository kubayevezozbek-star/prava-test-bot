from aiogram import Router, F, Bot
from aiogram.types import (
    Message, 
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    WebAppInfo
)
from aiogram.filters import CommandStart
import database as db
from config import ADMIN_USERNAME, WEBAPP_URL, VIP_PRICE_STR

router = Router()

def get_main_keyboard(webapp_url: str) -> ReplyKeyboardMarkup:
    buttons = []
    if webapp_url:
        buttons.append([KeyboardButton(text="🚗 Imtihonni boshlash", web_app=WebAppInfo(url=webapp_url))])
    else:
        buttons.append([KeyboardButton(text="🚗 Imtihonni boshlash")])

    buttons.append([
        KeyboardButton(text="👑 VIP obuna (30 000 so'm)"),
        KeyboardButton(text="👥 Do'stlarni taklif qilish")
    ])
    buttons.append([KeyboardButton(text="📞 Adminga murojaat")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Foydalanuvchi"
    username = message.from_user.username or ""

    # Referal parametrini ajratib olish
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            potential_ref = int(args[1].replace("ref_", ""))
            if potential_ref != user_id:
                referrer_id = potential_ref
        except ValueError:
            pass

    # Foydalanuvchini bazada saqlash / yangilash
    user = await db.get_or_create_user(user_id, first_name, username, referrer_id)

    # Agar do'st taklif qilgan bo'lsa, taklif qilganga xabar yuborish
    if referrer_id and user.get("referred_by") == referrer_id:
        try:
            await bot.send_message(
                referrer_id,
                f"🎉 <b>Ajoyib yangilik!</b>\n\n"
                f"Siz taklif qilgan do'stingiz (<b>{first_name}</b>) botga qo'shildi!\n"
                f"🎁 Sizga navbatdagi bilet bepul va doimiy ochildi!",
                parse_mode="HTML"
            )
        except Exception:
            pass

    caption = (
        f"Assalomu alaykum, <b>{first_name}</b>! 🚗\n\n"
        "<b>Prava Test AI</b> — O'zbekiston Yo'l Harakati Qoidalari (YHQ) bo'yicha rasmiy testlar va Davlat imtihon simulyatoriga xush kelibsiz!\n\n"
        "✨ <b>Imkoniyatlar:</b>\n"
        "• 🟢 <b>1, 2 va 3-biletlar</b> — mutlaqo bepul va doimiy ochiq!\n"
        "• ⏱ <b>20 daqiqalik</b> rasmiy Davlat imtihoni rejimi;\n"
        "• 📸 <b>Haqiqiy imtihon rasmlari</b> va savollari (rasmiy YHQ standarti);\n"
        "• 🤖 <b>AI Xatolar tahlili</b> — adashgan har bir savolingiz bo'yicha qoidani tushuntirib beradi;\n"
        "• 🔄 <b>Xatolar ustida ishlash</b> — noto'g'ri yechilgan savollarni qayta mashq qilish;\n"
        "• 👥 Har bir taklif qilingan do'st uchun +1 ta bepul bilet;\n"
        f"• 👑 <b>VIP obuna ({VIP_PRICE_STR})</b> — barcha biletlarni 3 oyga to'liq ochadi!\n\n"
        "Testni boshlash uchun quyidagi <b>'🚗 Imtihonni boshlash'</b> tugmasini bosing:"
    )

    await message.answer(
        caption,
        parse_mode="HTML",
        reply_markup=get_main_keyboard(WEBAPP_URL)
    )

@router.message(F.text == "🚗 Imtihonni boshlash")
async def open_app_button(message: Message, bot: Bot):
    if WEBAPP_URL:
        ikb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📱 Mini Appni ochish", web_app=WebAppInfo(url=WEBAPP_URL))]
        ])
    else:
        ikb = None

    await message.answer(
        "🚗 Test va biletlarni yechish uchun quyidagi tugmani bosing:",
        reply_markup=ikb
    )

@router.message(F.text == "📞 Adminga murojaat")
async def contact_admin(message: Message):
    text = (
        "📞 <b>Administrator bilan aloqa</b>\n\n"
        "Savollar, takliflar yoki to'lov bo'yicha yordam kerak bo'lsa, adminga yozishingiz mumkin:\n\n"
        f"👉 <b>Admin:</b> @{ADMIN_USERNAME}"
    )
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Adminga yozish", url=f"https://t.me/{ADMIN_USERNAME}")]
    ])
    await message.answer(text, parse_mode="HTML", reply_markup=ikb)

@router.message(F.text == "👥 Do'stlarni taklif qilish")
async def invite_friends_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    bot_info = await bot.get_me()
    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"

    text = (
        "🎁 <b>Do'stlarni taklif qiling va bepul biletlar oching!</b>\n\n"
        "Har bir do'stingiz sizning havolangiz orqali botga kirganda, sizga <b>navbatdagi 1 ta bilet</b> bepul va butunlay ochiladi!\n\n"
        f"🔗 <b>Sizning shaxsiy taklif havolangiz:</b>\n"
        f"<code>{ref_link}</code>"
    )

    share_text = "🚗 Prava imtihoniga tayyorgarlik ko'rish uchun rasmiy YHQ test boti! Sinab ko'ring:"
    share_url = f"https://t.me/share/url?url={ref_link}&text={share_text}"

    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📲 Do'stlarga ulashish", url=share_url)]
    ])

    await message.answer(text, parse_mode="HTML", reply_markup=ikb)
