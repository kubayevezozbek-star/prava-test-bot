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
from config import ADMIN_USERNAME, WEBAPP_URL, PRICE_3_TICKETS_STR, PRICE_VIP_90_STR, PRICE_EXAM_1_STR

router = Router()

def get_main_keyboard(webapp_url: str) -> ReplyKeyboardMarkup:
    buttons = []
    if webapp_url:
        buttons.append([KeyboardButton(text="🚗 Imtihonni boshlash", web_app=WebAppInfo(url=webapp_url))])
    else:
        buttons.append([KeyboardButton(text="🚗 Imtihonni boshlash")])

    buttons.append([
        KeyboardButton(text="📊 Tayyorgarlik darajam"),
        KeyboardButton(text="💎 Tariflar va Xarid")
    ])
    buttons.append([
        KeyboardButton(text="👥 Do'stlarni taklif qilish"),
        KeyboardButton(text="📞 Adminga murojaat")
    ])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Foydalanuvchi"
    username = message.from_user.username or ""

    # Referal parametrini tekshirish
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            potential_ref = int(args[1].replace("ref_", ""))
            if potential_ref != user_id:
                referrer_id = potential_ref
        except ValueError:
            pass

    # Foydalanuvchini ro'yxatga olish
    user = await db.get_or_create_user(user_id, first_name, username, referrer_id)

    # Agar do'st taklif qilingan bo'lsa, taklif qilganga xabar yuborish
    ref_res = user.get("ref_result")
    if referrer_id and ref_res:
        try:
            total_refs = ref_res.get("total_referrals", 1)
            opened_ticket = ref_res.get("opened_ticket")
            vip_granted = ref_res.get("vip_granted", False)

            if vip_granted:
                msg = (
                    f"🏆 <b>TABRIKLAYMIZ!</b>\n\n"
                    f"Siz taklif qilgan do'stingiz (<b>{first_name}</b>) qo'shildi va jami takliflaringiz <b>{total_refs} taga</b> yetdi!\n\n"
                    f"👑 Sizga <b>3 OYLIK (90 kunlik) TO'LIQ VIP OBUNA</b> (qiymati 30 000 so'm) MUTLAQO BEPUL taqdim etildi!\n\n"
                    f"🚗 Endi barcha 60 ta bilet va cheksiz Davlat imtihonlari siz uchun to'liq ochiq!"
                )
            else:
                ticket_info = f"🎁 Sizga navbatdagi <b>{opened_ticket}-bilet</b> bepul ochildi!\n" if opened_ticket else ""
                rem = max(0, 10 - total_refs)
                msg = (
                    f"🎉 <b>Ajoyib yangilik!</b>\n\n"
                    f"Siz taklif qilgan do'stingiz (<b>{first_name}</b>) botga qo'shildi!\n"
                    f"{ticket_info}"
                    f"📊 Jami takliflaringiz: <b>{total_refs} / 10 ta</b>\n"
                    f"✨ Yana <b>{rem} ta</b> do'stingiz qo'shilsa, <b>3 oylik to'liq VIP obuna</b> bepul ochiladi!"
                )
            await bot.send_message(referrer_id, msg, parse_mode="HTML")
        except Exception:
            pass

    caption = (
        f"Assalomu alaykum, <b>{first_name}</b>! 🚗\n\n"
        "<b>Prava Test AI</b> — O'zbekiston Davlat haydovchilik guvohnomasi (YHQ) imtihon simulyatoriga xush kelibsiz!\n\n"
        "✨ <b>Asosiy imkoniyatlar:</b>\n"
        "• 🟢 <b>1–7 biletlar (140 ta savol)</b> — mutlaqo bepul va doimiy ochiq!\n"
        "• 🎁 <b>10 ta do'st taklif qiling</b> — 3 oylik VIP obuna (30 000 so'mlik) BEPUL!\n"
        f"• 📚 <b>Ixtiyoriy 3 ta bilet</b> — {PRICE_3_TICKETS_STR} (3 oy kafolatli);\n"
        f"• 🎟 <b>1 martalik Imtihon</b> — {PRICE_EXAM_1_STR};\n"
        "• ⚡ <b>30 kunlik Cheksiz Imtihon</b> — 15 000 so'm;\n"
        f"• 👑 <b>VIP To'liq Kirish (90 kun)</b> — {PRICE_VIP_90_STR};\n"
        "• 🌐 O'zbekcha (Lotin) va Ruscha til rejimlari.\n\n"
        "Sinovni boshlash uchun quyidagi <b>'🚗 Imtihonni boshlash'</b> tugmasini bosing:"
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
        "Savollar, to'lovlar yoki takliflar bo'yicha adminga to'g'ridan-to'g'ri murojaat qilishingiz mumkin:\n\n"
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
    ref_stats = await db.get_referral_stats(user_id)
    count = ref_stats["count"]
    rem = ref_stats["remaining"]

    # Progress bar
    total_blocks = 10
    filled = min(10, count)
    bar = "🟩" * filled + "⬜" * (total_blocks - filled)

    text = (
        "🎁 <b>Do'stlarni taklif qiling va 3 oylik VIP obunani BEPUL oling!</b>\n\n"
        f"📊 <b>Sizning takliflaringiz:</b> {count} / 10 ta do'st\n"
        f"{bar} <b>({ref_stats['percent']}%)</b>\n\n"
        "✨ Har bir taklif qilingan do'st uchun navbatdagi bilet bepul ochiladi.\n"
        "👑 <b>10 ta do'st</b> taklif qilganingizda, <b>90 kunlik to'liq VIP obuna</b> (qiymati 30 000 so'm) mutlaqo bepul sovg'a qilinadi!\n\n"
        f"<i>(Yana {rem} ta do'stingiz qo'shilsa VIP avtomatik ochiladi!)</i>\n\n"
        f"🔗 <b>Sizning taklif havolangiz:</b>\n"
        f"<code>{ref_link}</code>"
    )

    share_text = "🚗 Prava (YHQ) imtihoniga tayyorgarlik ko'rish uchun eng zo'r rasmiy test boti! Sinab ko'ring:"
    share_url = f"https://t.me/share/url?url={ref_link}&text={share_text}"

    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📲 Do'stlarga ulashish", url=share_url)],
        [InlineKeyboardButton(text="🚗 Testlarni boshlash", web_app=WebAppInfo(url=WEBAPP_URL))] if WEBAPP_URL else []
    ])

    await message.answer(text, parse_mode="HTML", reply_markup=ikb)

@router.message(F.text.in_(["📊 Tayyorgarlik darajam", "/stats", "/progress", "/my"]))
async def user_progress_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Foydalanuvchi"

    stats = await db.get_user_learning_stats(user_id, 1200)
    access = await db.get_user_access(user_id)
    streak = await db.update_user_streak(user_id)

    # Progress bar yasash (masalan: [■■■■□□□□□□] 40%)
    total_blocks = 10
    filled = int(stats["percent"] // 10)
    bar = "🟩" * filled + "⬜" * (total_blocks - filled)

    status_str = "Oddiy"
    if access["is_vip"]:
        status_str = "👑 VIP obunachi"
    elif access["has_exam_pass"]:
        status_str = "⚡ Cheksiz imtihon obunachisi"

    text = (
        f"📊 <b>{first_name}, sizning tayyorgarlik darajangiz:</b>\n\n"
        f"🎯 <b>O'zlashtirish:</b> <b>{stats['percent']}%</b>\n"
        f"{bar}\n\n"
        f"📚 <b>O'rganilgan savollar:</b> {stats['learned_count']} / 1200 ta\n"
        f"❌ <b>Xatoliklar (qayta ishlash kerak):</b> {stats['mistakes_count']} ta\n"
        f"🔮 <b>AI Imtihondan o'tish ehtimoli:</b> <b>{stats['pass_prob']}%</b>\n"
        f"🎖 <b>Darajangiz:</b> {stats['level_badge']} <b>{stats['level_uz']}</b>\n"
        f"🔥 <b>Faollik seriyasi:</b> <b>{streak} kun</b> davom etmoqda\n"
        f"💎 <b>Obuna holati:</b> {status_str}\n\n"
        "💡 <i>Har kuni 1-2 ta bilet ishlab borsangiz, o'tish ehtimolingiz 95%+ ga yetadi!</i>"
    )

    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚗 Testlarni boshlash", web_app=WebAppInfo(url=WEBAPP_URL))] if WEBAPP_URL else []
    ])

    await message.answer(text, parse_mode="HTML", reply_markup=ikb if WEBAPP_URL else None)
