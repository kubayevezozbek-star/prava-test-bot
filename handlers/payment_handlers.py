from aiogram import Router, F, Bot
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
import database as db
from config import (
    ADMIN_ID,
    CARD_NUMBER,
    CARD_HOLDER,
    PRICE_3_TICKETS,
    PRICE_3_TICKETS_STR,
    PRICE_EXAM_1,
    PRICE_EXAM_1_STR,
    PRICE_EXAM_30,
    PRICE_EXAM_30_STR,
    PRICE_VIP_90,
    PRICE_VIP_90_STR
)

router = Router()

class PaymentStates(StatesGroup):
    waiting_for_tickets_input = State()
    waiting_for_receipt = State()

def get_tarifs_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📚 Ixtiyoriy 3 ta bilet — {PRICE_3_TICKETS_STR}", callback_data="buy_tickets_3")],
        [InlineKeyboardButton(text=f"🎟 1 martalik Imtihon — {PRICE_EXAM_1_STR}", callback_data="buy_exam_1")],
        [InlineKeyboardButton(text=f"⚡ 30 kunlik Cheksiz Imtihon — {PRICE_EXAM_30_STR}", callback_data="buy_exam_30")],
        [InlineKeyboardButton(text=f"👑 VIP To'liq Kirish (90 kun) — {PRICE_VIP_90_STR}", callback_data="buy_vip_90")]
    ])

@router.message(F.text.in_(["💎 Tariflar va Xarid", "/tarifs", "/buy", "/vip"]))
async def show_tarifs_menu(message: Message):
    user_id = message.from_user.id
    access = await db.get_user_access(user_id)

    status_str = "Oddiy"
    if access["is_vip"]:
        status_str = f"👑 VIP ({access['vip_until'][:10]} gacha)"
    elif access["has_exam_pass"]:
        status_str = f"⚡ Imtihon obunasi ({access['exam_pass_until'][:10]} gacha)"

    text = (
        "💎 <b>Rasmiy Prava Test — Tariflar va Xarid</b>\n\n"
        f"📊 Sizning holatingiz: <b>{status_str}</b>\n"
        f"🟢 Ochiq biletlaringiz: <b>{len(access['unlocked_tickets'])} ta</b>\n"
        f"🎟 Mavjud imtihon urinishlari: <b>{access['exam_attempts']} ta</b>\n\n"
        "Quyidagi xizmatlardan birini tanlang:"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=get_tarifs_keyboard())

# 1. 3 ta bilet sotib olish
@router.callback_query(F.data == "buy_tickets_3")
async def process_buy_3_tickets(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(PaymentStates.waiting_for_tickets_input)
    
    text = (
        f"📚 <b>3 ta bilet sotib olish ({PRICE_3_TICKETS_STR})</b>\n\n"
        "O'zingizga kerakli bo'lgan <b>3 ta bilet raqamini</b> yozib yuboring.\n"
        "<i>(Masalan: 4, 5, 6 yoki 12, 15, 20)</i>\n\n"
        "Ochilgan biletlar sizda <b>3 oy (90 kun)</b> saqlanadi."
    )
    await callback.message.answer(text, parse_mode="HTML")

@router.message(PaymentStates.waiting_for_tickets_input, F.text)
async def process_tickets_chosen(message: Message, state: FSMContext):
    raw_text = message.text
    # Ajratish
    import re
    numbers = [int(n) for n in re.findall(r'\b\d+\b', raw_text) if 1 <= int(n) <= 60]
    
    if len(numbers) < 1:
        await message.answer("⚠️ Iltimos, kamida 1 tadan 3 tagacha bilet raqamini yozing (masalan: 4, 5, 6):")
        return

    # Faqat dastlabki 3 tasini olish
    chosen = numbers[:3]
    chosen_str = ", ".join(str(n) for n in chosen)

    await state.set_state(PaymentStates.waiting_for_receipt)
    await state.update_data(
        payment_type="tickets_3",
        details=f"Tanlangan 3 ta bilet: {chosen_str}",
        ticket_numbers=chosen_str,
        amount=PRICE_3_TICKETS
    )

    text = (
        f"💳 <b>To'lov ma'lumotlari</b>\n\n"
        f"📦 Xarid: <b>{chosen_str}-biletlar</b>\n"
        f"💰 Summa: <b>{PRICE_3_TICKETS_STR}</b> (90 kun muddatga)\n\n"
        f"💳 Karta raqami: <code>{CARD_NUMBER}</code>\n"
        f"👤 Karta egasi: <b>{CARD_HOLDER}</b>\n\n"
        "📌 <i>To'lovni amalga oshirgach, to'lov cheki skrinshotini shu yerga rasm qilib yuboring:</i>"
    )
    await message.answer(text, parse_mode="HTML")

# 2. 1 martalik imtihon
@router.callback_query(F.data == "buy_exam_1")
async def process_buy_exam_1(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(PaymentStates.waiting_for_receipt)
    await state.update_data(
        payment_type="exam_1",
        details="1 martalik 20 talik Imtihon",
        ticket_numbers="",
        amount=PRICE_EXAM_1
    )

    text = (
        f"🎟 <b>1 martalik Imtihon uchun to'lov</b>\n\n"
        f"💰 Narxi: <b>{PRICE_EXAM_1_STR}</b>\n"
        "Imkoniyat: 1 marta 20 talik rasmiy Davlat imtihoni simulyatorini topshirish.\n\n"
        f"💳 Karta raqami: <code>{CARD_NUMBER}</code>\n"
        f"👤 Karta egasi: <b>{CARD_HOLDER}</b>\n\n"
        "📌 <i>To'lov cheki skrinshotini shu yerga yuboring:</i>"
    )
    await callback.message.answer(text, parse_mode="HTML")

# 3. 30 kunlik imtihon
@router.callback_query(F.data == "buy_exam_30")
async def process_buy_exam_30(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(PaymentStates.waiting_for_receipt)
    await state.update_data(
        payment_type="exam_30",
        details="30 kunlik Cheksiz Imtihon",
        ticket_numbers="",
        amount=PRICE_EXAM_30
    )

    text = (
        f"⚡ <b>30 kunlik Cheksiz Imtihon uchun to'lov</b>\n\n"
        f"💰 Narxi: <b>{PRICE_EXAM_30_STR}</b>\n"
        "Imkoniyat: 30 kun davomida istalgancha 20 talik aralash imtihonlarni cheksiz topshirish!\n\n"
        f"💳 Karta raqami: <code>{CARD_NUMBER}</code>\n"
        f"👤 Karta egasi: <b>{CARD_HOLDER}</b>\n\n"
        "📌 <i>To'lov cheki skrinshotini shu yerga yuboring:</i>"
    )
    await callback.message.answer(text, parse_mode="HTML")

# 4. VIP 90 kunlik
@router.callback_query(F.data == "buy_vip_90")
async def process_buy_vip_90(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(PaymentStates.waiting_for_receipt)
    await state.update_data(
        payment_type="vip_90",
        details="VIP 90 kunlik To'liq Kirish",
        ticket_numbers="",
        amount=PRICE_VIP_90
    )

    text = (
        f"👑 <b>VIP To'liq Kirish (90 kun) uchun to'lov</b>\n\n"
        f"💰 Narxi: <b>{PRICE_VIP_90_STR}</b>\n"
        "Imkoniyat: Barcha 60 ta bilet (1200 ta savol) + cheksiz 20 talik imtihonlar 3 oyga to'liq ochiladi!\n\n"
        f"💳 Karta raqami: <code>{CARD_NUMBER}</code>\n"
        f"👤 Karta egasi: <b>{CARD_HOLDER}</b>\n\n"
        "📌 <i>To'lov cheki skrinshotini shu yerga yuboring:</i>"
    )
    await callback.message.answer(text, parse_mode="HTML")

# Chek qabul qilish
@router.message(PaymentStates.waiting_for_receipt, F.photo)
@router.message(F.photo)
async def handle_payment_receipt(message: Message, state: FSMContext, bot: Bot):
    user_id = message.from_user.id
    first_name = message.from_user.first_name or "Foydalanuvchi"
    username = message.from_user.username or ""

    data = await state.get_data()
    pending = await db.get_pending_selection(user_id)

    if pending:
        ptype = pending.get("payment_type", "vip_90")
        details = pending.get("details", "VIP To'liq Kirish (90 kun)")
        ticket_numbers = pending.get("ticket_numbers", "")
        amount = pending.get("amount", PRICE_VIP_90)
        await db.clear_pending_selection(user_id)
    elif data.get("payment_type"):
        ptype = data.get("payment_type", "vip_90")
        details = data.get("details", "VIP To'liq Kirish (90 kun)")
        ticket_numbers = data.get("ticket_numbers", "")
        amount = data.get("amount", PRICE_VIP_90)
    else:
        ptype = "vip_90"
        details = "VIP To'liq Kirish (90 kun)"
        ticket_numbers = ""
        amount = PRICE_VIP_90

    file_id = message.photo[-1].file_id

    payment_id = await db.create_payment(
        telegram_id=user_id,
        payment_type=ptype,
        details=details,
        ticket_numbers=ticket_numbers,
        amount=amount,
        receipt_photo_id=file_id
    )
    await state.clear()

    await message.answer(
        "✅ <b>To'lov chekingiz qabul qilindi!</b>\n\n"
        f"📦 Xarid: <b>{details}</b>\n"
        f"💵 Summa: <b>{amount:,} so'm</b>\n\n"
        "Chek adminga tekshirish uchun yuborildi. Administrator tekshirib tasdiqlashi bilan "
        "xizmatingiz darhol ishga tushadi 🚗",
        parse_mode="HTML"
    )

    # Adminga yuborish
    admin_caption = (
        f"🔔 <b>YANGI TO'LOV CHEKI! (№{payment_id})</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {first_name}\n"
        f"🆔 <b>ID:</b> <code>{user_id}</code>\n"
        f"🔗 <b>Username:</b> @{username or 'mavjud emas'}\n"
        f"📦 <b>Xarid turi:</b> {details}\n"
        f"💵 <b>Summa:</b> {amount:,} so'm\n\n"
        "Chekni tekshirib, qarorni tanlang:"
    )

    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"adm_app_{payment_id}"),
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
