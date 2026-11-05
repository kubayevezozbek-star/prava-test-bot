from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import database as db
from config import ADMIN_ID, CARD_NUMBER, CARD_HOLDER, VIP_PRICE_STR, VIP_PRICE

router = Router()

class PaymentStates(StatesGroup):
    waiting_for_receipt = State()

@router.message(F.text.startswith("👑 VIP obuna"))
@router.message(F.text == "/vip")
async def show_vip_info(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user = await db.get_user(user_id)
    
    vip_status = "❌ Faol emas"
    if user and user.get("is_vip"):
        vip_status = f"✅ Faol ({user.get('vip_until')} gacha)"

    text = (
        "👑 <b>VIP OBUNA — Rasmiy Testlar To'plami</b>\n\n"
        f"📊 Sizning VIP holatingiz: <b>{vip_status}</b>\n\n"
        "✨ <b>VIP obuna nimalarni beradi?</b>\n"
        "• Barcha biletlarga to'liq va cheklovsiz kirish;\n"
        "• 1200 ta rasmiy Davlat imtihoni savollari va rasmlari;\n"
        "• Xatolar ustida ishlash bo'limi;\n"
        "• <b>3 oy (90 kun)</b> kafolatlangan doimiy ruxsat.\n\n"
        f"💰 Narxi: <b>{VIP_PRICE_STR}</b> (90 kun uchun)\n\n"
        f"💳 Karta raqami: <code>{CARD_NUMBER}</code>\n"
        f"👤 Karta egasi: <b>{CARD_HOLDER}</b>\n\n"
        "📌 <i>To'lovni amalga oshirgach, to'lov cheki skrinshotini (rasmini) botga yuboring:</i>"
    )

    await state.set_state(PaymentStates.waiting_for_receipt)
    await message.answer(text, parse_mode="HTML")

@router.message(PaymentStates.waiting_for_receipt, F.photo)
@router.message(F.photo)
async def handle_payment_receipt(message: Message, state: FSMContext, bot: Bot):
    file_id = message.photo[-1].file_id
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Foydalanuvchi"
    username = message.from_user.username or ""

    payment_id = await db.create_payment(user_id, file_id, VIP_PRICE)
    await state.clear()

    await message.answer(
        "✅ <b>To'lov chekingiz muvaffaqiyatli qabul qilindi!</b>\n\n"
        "Chek adminga tekshirish uchun yuborildi. Administrator tekshirib tasdiqlashi bilan "
        "barcha biletlar <b>3 oyga</b> avtomatik ochiladi 🚗",
        parse_mode="HTML"
    )

    # Adminga yuborish
    admin_caption = (
        f"🔔 <b>YANGI TO'LOV CHEKI! (№{payment_id})</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {first_name}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"🔗 <b>Username:</b> @{username or 'mavjud emas'}\n"
        f"💵 <b>To'lov miqdori:</b> {VIP_PRICE_STR} (VIP 90 kun)\n\n"
        "Chekni tekshirib, qarorni tanlang:"
    )

    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash (90 kun VIP)", callback_data=f"adm_app_{payment_id}"),
            InlineKeyboardButton(text="❌ Rad etish", callback_data=f"adm_rej_{payment_id}")
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
