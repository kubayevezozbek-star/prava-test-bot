import asyncio
from aiogram import Router, F, Bot
from aiogram.types import (
    Message, 
    CallbackQuery,
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton,
    WebAppInfo
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramAPIError

import database as db
from config import ADMIN_ID, CARD_NUMBER, CARD_HOLDER, ADMIN_USERNAME, PACKAGES, WEBAPP_URL

router = Router()

class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirm = State()

class PaymentStates(StatesGroup):
    waiting_for_receipt = State()

def get_main_keyboard(webapp_url: str) -> ReplyKeyboardMarkup:
    # If webapp_url is set, provide WebApp button, else provide a placeholder button
    buttons = []
    if webapp_url:
        buttons.append([KeyboardButton(text="📱 Imtihonni boshlash", web_app=WebAppInfo(url=webapp_url))])
    else:
        buttons.append([KeyboardButton(text="📱 Imtihonni boshlash")])

    buttons.append([
        KeyboardButton(text="💳 Bilet sotib olish"),
        KeyboardButton(text="👥 Do'stlarni taklif qilish")
    ])
    buttons.append([KeyboardButton(text="📞 Adminga murojaat")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def get_packages_inline_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for key, pkg in PACKAGES.items():
        buttons.append([
            InlineKeyboardButton(text=f"{pkg['title']} — {pkg['price_str']}", callback_data=f"buy_{key}")
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Foydalanuvchi"
    username = message.from_user.username or ""

    # Parse referral argument
    args = message.text.split()
    referrer_id = None
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            potential_ref = int(args[1].replace("ref_", ""))
            if potential_ref != user_id:
                referrer_id = potential_ref
        except ValueError:
            pass

    # Yangi yoki mavjud foydalanuvchini bazaga kiritish
    user = await db.get_or_create_user(user_id, first_name, username, referrer_id)

    # Agar do'st taklif qilgan bo'lsa, taklif qilganga xabar boradi
    if referrer_id and user.get("referrer_id") == referrer_id:
        try:
            ref_user = await db.get_user(referrer_id)
            new_ticket = ref_user["unlocked_max_ticket"] if ref_user else "yangi"
            await bot.send_message(
                referrer_id,
                f"🎉 <b>Ajoyib yangilik!</b>\n\n"
                f"Siz taklif qilgan do'stingiz (<b>{first_name}</b>) botga qo'shildi!\n"
                f"🎁 Sizga <b>{new_ticket}-bilet</b> bepul ochildi!",
                parse_mode="HTML"
            )
        except Exception:
            pass

    # Botning WebApp havolasi (agar WEBAPP_URL bo'lsa)
    bot_info = await bot.get_me()
    app_url = WEBAPP_URL if WEBAPP_URL else f"https://t.me/{bot_info.username}/app"

    caption = (
        f"Assalomu alaykum, <b>{first_name}</b>! 🚗\n\n"
        "<b>AvtoTest YHQ</b> — O'zbekiston Davlat haydovchilik guvohnomasi (prava) imtihoniga tayyorlovchi rasmiy botga xush kelibsiz!\n\n"
        "✨ <b>Imkoniyatlar:</b>\n"
        "• 🟢 <b>1–3 biletlar (60 ta savol)</b> — butunlay bepul!\n"
        "• ⏱ 20 daqiqalik haqiqiy Davlat imtihoni simulyatori;\n"
        "• 🤖 <b>AI Xatolar tahlili</b> — adashgan savollaringizni eslab qoladi va qoidani tushuntiradi;\n"
        "• 👥 Har bir taklif qilingan do'st uchun +1 ta bepul bilet;\n"
        "• 💳 Ochilgan biletlar <b>3 oy davomida</b> saqlanadi.\n\n"
        "Imtihonni boshlash uchun quyidagi <b>'📱 Imtihonni boshlash'</b> tugmasini bosing:"
    )

    await message.answer(
        caption,
        parse_mode="HTML",
        reply_markup=get_main_keyboard(WEBAPP_URL)
    )

# "📱 Imtihonni boshlash" agar oddiy xabar bo'lsa
@router.message(F.text == "📱 Imtihonni boshlash")
async def open_app_message(message: Message, bot: Bot):
    bot_info = await bot.get_me()
    app_url = WEBAPP_URL if WEBAPP_URL else f"https://t.me/{bot_info.username}/app"
    
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

# "📞 Adminga murojaat"
@router.message(F.text == "📞 Adminga murojaat")
async def contact_admin(message: Message):
    text = (
        "📞 <b>Administrator bilan aloqa</b>\n\n"
        f"Savollar, takliflar yoki to'lov bo'yicha yordam kerak bo'lsa, adminga yozishingiz mumkin:\n\n"
        f"👉 <b>Admin:</b> @{ADMIN_USERNAME}"
    )
    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✉️ Adminga yozish", url=f"https://t.me/{ADMIN_USERNAME}")]
    ])
    await message.answer(text, parse_mode="HTML", reply_markup=ikb)

# "👥 Do'stlarni taklif qilish"
@router.message(F.text == "👥 Do'stlarni taklif qilish")
async def invite_friends_handler(message: Message, bot: Bot):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    bot_info = await bot.get_me()

    ref_link = f"https://t.me/{bot_info.username}?start=ref_{user_id}"
    invited = user.get("invited_count", 0) if user else 0

    text = (
        "🎁 <b>Do'stlarni taklif qiling va bepul biletlar yuting!</b>\n\n"
        "Har bir do'stingiz sizning havolangiz orqali botga kirsa, sizga <b>1 ta yangi bilet</b> bepul ochiladi!\n\n"
        f"👥 Siz taklif qilgan do'stlar soni: <b>{invited} ta</b>\n\n"
        f"🔗 <b>Sizning shaxsiy taklif havolangiz:</b>\n"
        f"<code>{ref_link}</code>"
    )

    share_text = "🚗 Prava imtihoniga tayyorgarlik ko'rish uchun ajoyib YHQ test boti! Sinab ko'ring:"
    share_url = f"https://t.me/share/url?url={ref_link}&text={share_text}"

    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📲 Do'stlarga ulashish", url=share_url)]
    ])

    await message.answer(text, parse_mode="HTML", reply_markup=ikb)

# "💳 Bilet sotib olish"
@router.message(F.text == "💳 Bilet sotib olish")
async def buy_tickets_menu(message: Message):
    user = await db.get_user(message.from_user.id)
    unlocked = user.get("unlocked_max_ticket", 3) if user else 3
    vip_status = f"Muddati: {user.get('vip_until')}" if user and user.get("vip_until") else "Oddiy"

    text = (
        "💳 <b>Biletlar to'plami va tariflar</b>\n\n"
        f"Sizda hozirda: <b>1–{unlocked} biletlar ochiq</b> ({vip_status})\n"
        "Ochilgan biletlar profilingizda <b>3 oy (90 kun)</b> kafolatli saqlanadi.\n\n"
        "Quyidagi to'plamlardan birini tanlang:"
    )
    await message.answer(text, parse_mode="HTML", reply_markup=get_packages_inline_keyboard())

# Paket tanlanganda to'lov rekvizitlari
@router.callback_query(F.data.startswith("buy_"))
async def process_buy_package(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    pkg_key = callback.data.replace("buy_", "")
    pkg = PACKAGES.get(pkg_key)
    if not pkg:
        return

    await state.set_state(PaymentStates.waiting_for_receipt)
    await state.update_data(package_key=pkg_key)

    text = (
        f"💳 <b>{pkg['title']} uchun to'lov</b>\n\n"
        f"💰 Narxi: <b>{pkg['price_str']}</b>\n"
        f"⏳ Muddati: <b>3 oy (90 kun)</b>\n\n"
        f"💳 Karta raqam: <code>{CARD_NUMBER}</code>\n"
        f"👤 Karta egasi: <b>{CARD_HOLDER}</b>\n\n"
        "📌 <i>To'lovni amalga oshirgach, to'lov cheki skrinshotini (rasmini) shu yerga yuboring:</i>"
    )
    await callback.message.answer(text, parse_mode="HTML")

# To'lov chekini qabul qilish
@router.message(F.photo)
async def receive_payment_receipt(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    pkg_key = data.get("package_key", "pack_4_6")
    pkg = PACKAGES.get(pkg_key, PACKAGES["pack_4_6"])

    file_id = message.photo[-1].file_id
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Foydalanuvchi"
    username = message.from_user.username or ""

    receipt_id = await db.create_receipt(user_id, pkg_key, file_id)
    await state.clear()

    await message.answer(
        "✅ <b>To'lov chekingiz qabul qilindi!</b>\n\n"
        "Chek adminga yuborildi. Administrator tekshirib tasdiqlashi bilan biletlaringiz "
        "<b>3 oyga</b> avtomatik ochiladi.",
        parse_mode="HTML"
    )

    # Adminga yuborish
    admin_caption = (
        f"🔔 <b>Yangi to'lov cheki! (№{receipt_id})</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {first_name}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"🔗 <b>Username:</b> @{username or 'mavjud emas'}\n"
        f"📦 <b>To'plam:</b> {pkg['title']}\n"
        f"💵 <b>Summa:</b> {pkg['price_str']}\n\n"
        "Chekni tekshirib tasdiqlang yoki rad eting:"
    )

    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash (3 oy)", callback_data=f"adm_app_{receipt_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"adm_rej_{receipt_id}")
        ]
    ])

    try:
        await bot.send_photo(
            chat_id=ADMIN_ID,
            photo=file_id,
            caption=admin_caption,
            parse_mode="HTML",
            reply_markup=ikb
        )
    except Exception as e:
        print(f"Adminga chek yuborishda xatolik: {e}")

# Admin Panel (/admin)
@router.message(Command("admin"))
async def admin_dashboard(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    stats = await db.get_stats()

    text = (
        "👑 <b>AvtoTest Boshqaruv Paneli (Admin)</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b> ta\n"
        f"💎 Pullik bilet olganlar: <b>{stats['paid_users']}</b> ta\n"
        f"📝 Jami ishlangan testlar: <b>{stats['total_tests']}</b> ta\n"
        f"⏳ Kutilayotgan cheklar: <b>{stats['pending_receipts']}</b> ta\n\n"
        "Barcha foydalanuvchilarga xabar yoki reklama yuborish uchun pastdagi tugmani bosing:"
    )

    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Reklama / Xabar yuborish", callback_data="start_broadcast")]
    ])

    await message.answer(text, parse_mode="HTML", reply_markup=ikb)

# Reklama yuborishni boshlash
@router.message(Command("reklama"))
@router.callback_query(F.data == "start_broadcast")
async def start_broadcast(event: Message | CallbackQuery, state: FSMContext):
    user_id = event.from_user.id
    if user_id != ADMIN_ID:
        return

    if isinstance(event, CallbackQuery):
        await event.answer()
        msg = event.message
    else:
        msg = event

    await state.set_state(BroadcastStates.waiting_for_message)
    await msg.answer(
        "📢 <b>Barcha foydalanuvchilarga reklama yuborish</b>\n\n"
        "A'zolarga yubormoqchi bo'lgan xabaringizni (matn, rasm, post) shu yerga yuboring:",
        parse_mode="HTML"
    )

@router.message(BroadcastStates.waiting_for_message)
async def process_broadcast_content(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        return

    await state.update_data(broadcast_msg_id=message.message_id)
    await state.set_state(BroadcastStates.waiting_for_confirm)

    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Ha, hammaga yuborilsin", callback_data="confirm_broadcast"),
            InlineKeyboardButton(text="❌ Bekor qilish", callback_data="cancel_broadcast")
        ]
    ])

    await message.reply(
        "👆 <b>Xabar qabul qilindi!</b>\n\nUshbu xabarni botning barcha foydalanuvchilariga yuborishni tasdiqlaysizmi?",
        parse_mode="HTML",
        reply_markup=ikb
    )

@router.callback_query(BroadcastStates.waiting_for_confirm, F.data == "confirm_broadcast")
async def execute_broadcast(callback: CallbackQuery, state: FSMContext, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        return

    await callback.answer("Yuborish boshlandi...")
    data = await state.get_data()
    msg_id = data.get("broadcast_msg_id")
    await state.clear()

    user_ids = await db.get_all_user_ids()
    sent_count = 0
    fail_count = 0

    await callback.message.edit_text("⏳ Reklama yuborilmoqda, kuting...")

    for uid in user_ids:
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=ADMIN_ID, message_id=msg_id)
            sent_count += 1
            await asyncio.sleep(0.05) # Flood limit safe
        except TelegramAPIError:
            fail_count += 1

    await bot.send_message(
        ADMIN_ID,
        f"📊 <b>Reklama yuborish yakunlandi!</b>\n\n"
        f"✅ Yetkazildi: <b>{sent_count}</b> ta\n"
        f"❌ Yetib bormadi (bloklagan): <b>{fail_count}</b> ta",
        parse_mode="HTML"
    )

@router.callback_query(BroadcastStates.waiting_for_confirm, F.data == "cancel_broadcast")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Bekor qilindi.")
    await callback.message.edit_text("❌ Reklama yuborish bekor qilindi.")

# Admin chekni tasdiqlash callback
@router.callback_query(F.data.startswith("adm_app_"))
async def admin_approve_receipt(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        return

    receipt_id = int(callback.data.replace("adm_app_", ""))
    res = await db.approve_receipt(receipt_id)
    if not res:
        await callback.answer("Bu chek allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    await callback.answer("✅ To'lov tasdiqlandi!")
    
    new_caption = (
        f"{callback.message.caption or ''}\n\n"
        f"✅ <b>TASDIQLANDI!</b>\n"
        f"Biletlar: <b>1–{res['new_max_ticket']}</b> ochildi.\n"
        f"Muddati: <b>{res['vip_until']}</b> gacha (3 oy)."
    )
    try:
        await callback.message.edit_caption(caption=new_caption, parse_mode="HTML", reply_markup=None)
    except Exception:
        pass

    # Foydalanuvchiga xabar yuborish
    try:
        user_msg = (
            "🎉 <b>Tabriklaymiz! To'lovingiz tasdiqlandi!</b>\n\n"
            f"📦 To'plam: <b>{res['package_title']}</b>\n"
            f"🟢 Biletlar: <b>1–{res['new_max_ticket']} biletlar</b> ochiq!\n"
            f"⏳ Amal qilish muddati: <b>{res['vip_until']}</b> gacha (3 oy).\n\n"
            "Endi Mini App orqali yangi biletlarni bemalol yechishingiz mumkin!"
        )
        await bot.send_message(res["user_id"], user_msg, parse_mode="HTML")
    except Exception:
        pass

# Admin chekni rad etish callback
@router.callback_query(F.data.startswith("adm_rej_"))
async def admin_reject_receipt(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        return

    receipt_id = int(callback.data.replace("adm_rej_", ""))
    user_id = await db.reject_receipt(receipt_id)
    if not user_id:
        await callback.answer("Bu chek allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    await callback.answer("❌ Rad etildi.")
    new_caption = f"{callback.message.caption or ''}\n\n❌ <b>RAD ETILDI!</b>"
    try:
        await callback.message.edit_caption(caption=new_caption, parse_mode="HTML", reply_markup=None)
    except Exception:
        pass

    try:
        await bot.send_message(
            user_id,
            "⚠️ <b>Afsuski, yuborgan to'lov chekingiz tasdiqlanmadi.</b>\n"
            "Agar xatolik yuz bergan bo'lsa, to'g'ri chekni qayta yuboring yoki adminga murojaat qiling.",
            parse_mode="HTML"
        )
    except Exception:
        pass
