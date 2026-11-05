import asyncio
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.exceptions import TelegramAPIError

import database as db
from config import ADMIN_ID

router = Router()

class BroadcastStates(StatesGroup):
    waiting_for_message = State()
    waiting_for_confirm = State()

@router.message(Command("admin"))
async def admin_dashboard(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    stats = await db.get_stats()

    text = (
        "👑 <b>Prava Test Boshqaruv Paneli (Admin)</b>\n\n"
        f"👥 Jami foydalanuvchilar: <b>{stats['total_users']}</b> ta\n"
        f"💎 VIP foydalanuvchilar: <b>{stats['vip_users']}</b> ta\n"
        f"📝 Jami ishlangan testlar: <b>{stats['total_tests']}</b> ta\n"
        f"⏳ Kutilayotgan to'lovlar: <b>{stats['pending_payments']}</b> ta\n"
        f"💰 Jami tushum: <b>{stats['total_earned']:,} so'm</b>\n\n"
        "Foydalanuvchilarga xabar yoki reklama tarqatish:"
    )

    ikb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Reklama / Xabar yuborish", callback_data="start_broadcast")]
    ])

    await message.answer(text, parse_mode="HTML", reply_markup=ikb)

# To'lovni tasdiqlash
@router.callback_query(F.data.startswith("adm_app_"))
async def admin_approve_payment(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        return

    payment_id = int(callback.data.replace("adm_app_", ""))
    res = await db.approve_payment(payment_id)
    if not res:
        await callback.answer("Bu to'lov allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    await callback.answer("✅ To'lov tasdiqlandi!")
    
    new_caption = (
        f"{callback.message.caption or ''}\n\n"
        f"✅ <b>TASDIQLANDI!</b>\n"
        f"VIP muddati: <b>{res['vip_until']}</b> gacha (90 kun)."
    )
    try:
        await callback.message.edit_caption(caption=new_caption, parse_mode="HTML", reply_markup=None)
    except Exception:
        pass

    # Foydalanuvchiga xabar yuborish
    try:
        user_msg = (
            "🎉 <b>Tabriklaymiz! To'lovingiz tasdiqlandi!</b>\n\n"
            "🚗 <b>Barcha biletlar 3 oy (90 kun) muddatga to'liq ochildi!</b>\n"
            f"📅 Amal qilish muddati: <b>{res['vip_until']}</b> gacha.\n\n"
            "Mini App orqali barcha biletlarni bemalol yechishingiz mumkin!"
        )
        await bot.send_message(res["telegram_id"], user_msg, parse_mode="HTML")
    except Exception as e:
        print(f"Foydalanuvchiga xabar yuborishda xatolik: {e}")

# To'lovni rad etish
@router.callback_query(F.data.startswith("adm_rej_"))
async def admin_reject_payment(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        return

    payment_id = int(callback.data.replace("adm_rej_", ""))
    user_id = await db.reject_payment(payment_id)
    if not user_id:
        await callback.answer("Bu to'lov allaqachon ko'rib chiqilgan!", show_alert=True)
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

# Reklama tarqatish (Broadcast)
@router.message(Command("reklama"))
@router.callback_query(F.data == "start_broadcast")
async def start_broadcast(event: Message | CallbackQuery, state: FSMContext):
    if event.from_user.id != ADMIN_ID:
        return

    if isinstance(event, CallbackQuery):
        await event.answer()
        msg = event.message
    else:
        msg = event

    await state.set_state(BroadcastStates.waiting_for_message)
    await msg.answer(
        "📢 <b>Barcha foydalanuvchilarga xabar yuborish</b>\n\n"
        "A'zolarga yubormoqchi bo'lgan xabaringizni (matn, rasm, video) shu yerga yuboring:",
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
        "👆 <b>Xabar qabul qilindi!</b>\n\nUshbu xabarni barcha foydalanuvchilarga yuborishni tasdiqlaysizmi?",
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

    await callback.message.edit_text("⏳ Xabar barcha foydalanuvchilarga yuborilmoqda, kuting...")

    for uid in user_ids:
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=ADMIN_ID, message_id=msg_id)
            sent_count += 1
            await asyncio.sleep(0.05)
        except TelegramAPIError:
            fail_count += 1

    await bot.send_message(
        ADMIN_ID,
        f"📊 <b>Xabar tarqatish yakunlandi!</b>\n\n"
        f"✅ Yetkazildi: <b>{sent_count}</b> ta\n"
        f"❌ Yetib bormadi (bloklagan): <b>{fail_count}</b> ta",
        parse_mode="HTML"
    )

@router.callback_query(BroadcastStates.waiting_for_confirm, F.data == "cancel_broadcast")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Bekor qilindi.")
    await callback.message.edit_text("❌ Xabar yuborish bekor qilindi.")
