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

def get_admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📢 Reklama / Xabar yuborish", callback_data="start_broadcast")],
        [InlineKeyboardButton(text="🔄 Statistikani yangilash", callback_data="refresh_stats")]
    ])

@router.message(Command("admin"))
async def admin_dashboard(message: Message):
    # Faqat bot egasi uchun qat'iy himoya
    if message.from_user.id != ADMIN_ID:
        return

    stats = await db.get_stats()

    text = (
        "👑 <b>Prava Test — Boshqaruv Paneli (ADMIN)</b>\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {stats['total_users']} ta\n"
        f"👑 <b>VIP a'zolar:</b> {stats['vip_users']} ta\n"
        f"⚡ <b>Imtihon obunachilari:</b> {stats['exam_pass_users']} ta\n"
        f"📝 <b>Ishlangan testlar soni:</b> {stats['total_tests']} ta\n"
        f"⏳ <b>Kutilayotgan to'lov cheklari:</b> {stats['pending_payments']} ta\n"
        f"💰 <b>Jami tushum (Kassada):</b> {stats['total_earned']:,} so'm\n\n"
        "Quyidagi tugmalar orqali botni boshqarishingiz mumkin:"
    )

    await message.answer(text, parse_mode="HTML", reply_markup=get_admin_keyboard())

@router.callback_query(F.data == "refresh_stats")
async def refresh_stats_handler(callback: CallbackQuery):
    if callback.from_user.id != ADMIN_ID:
        return
    await callback.answer("Statistika yangilandi!")
    stats = await db.get_stats()
    text = (
        "👑 <b>Prava Test — Boshqaruv Paneli (ADMIN)</b>\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {stats['total_users']} ta\n"
        f"👑 <b>VIP a'zolar:</b> {stats['vip_users']} ta\n"
        f"⚡ <b>Imtihon obunachilari:</b> {stats['exam_pass_users']} ta\n"
        f"📝 <b>Ishlangan testlar soni:</b> {stats['total_tests']} ta\n"
        f"⏳ <b>Kutilayotgan to'lov cheklari:</b> {stats['pending_payments']} ta\n"
        f"💰 <b>Jami tushum (Kassada):</b> {stats['total_earned']:,} so'm\n\n"
        "Quyidagi tugmalar orqali botni boshqarishingiz mumkin:"
    )
    try:
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_admin_keyboard())
    except Exception:
        pass

# Chekni tasdiqlash
@router.callback_query(F.data.startswith("adm_app_"))
async def admin_approve_payment(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id != ADMIN_ID:
        return

    payment_id = int(callback.data.replace("adm_app_", ""))
    res = await db.approve_payment(payment_id)
    if not res:
        await callback.answer("Bu to'lov allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    await callback.answer("✅ To'lov muvaffaqiyatli tasdiqlandi!")
    
    new_caption = (
        f"{callback.message.caption or ''}\n\n"
        f"✅ <b>TASDIQLANDI!</b>\n"
        f"🎁 <b>Ochildi:</b> {res['opened_desc']}"
    )
    try:
        await callback.message.edit_caption(caption=new_caption, parse_mode="HTML", reply_markup=None)
    except Exception:
        pass

    # Foydalanuvchiga xabar
    try:
        user_msg = (
            "🎉 <b>Tabriklaymiz! To'lovingiz tasdiqlandi!</b>\n\n"
            f"✅ <b>Sizga ochildi:</b> {res['opened_desc']}\n\n"
            "Endi Mini App'ga kirib bemalol test va imtihonlarni topshirishingiz mumkin! 🚗💨"
        )
        await bot.send_message(res["telegram_id"], user_msg, parse_mode="HTML")
    except Exception as e:
        print(f"Foydalanuvchiga xabar yuborishda xatolik: {e}")

# Chekni rad etish
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
            "⚠️ <b>Yuborgan to'lov chekingiz tasdiqlanmadi.</b>\n"
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
        "📢 <b>Barcha foydalanuvchilarga reklama / xabar yuborish</b>\n\n"
        "Yubormoqchi bo'lgan postingizni (matn, rasm, video yoki audio) shu yerga yuboring:",
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
        "👆 <b>Xabaringiz qabul qilindi!</b>\n\nUshbu xabarni barcha foydalanuvchilarga tarqatishni tasdiqlaysizmi?",
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

    status_msg = await callback.message.edit_text("⏳ Xabar barcha foydalanuvchilarga yuborilmoqda, kuting...")

    for uid in user_ids:
        try:
            await bot.copy_message(chat_id=uid, from_chat_id=ADMIN_ID, message_id=msg_id)
            sent_count += 1
            await asyncio.sleep(0.04)
        except TelegramAPIError:
            fail_count += 1

    await bot.send_message(
        ADMIN_ID,
        f"📊 <b>Reklama yuborish yakunlandi!</b>\n\n"
        f"✅ Muvaffaqiyatli yetkazildi: <b>{sent_count}</b> ta\n"
        f"❌ Yetib bormadi (bloklagan): <b>{fail_count}</b> ta",
        parse_mode="HTML"
    )

@router.callback_query(BroadcastStates.waiting_for_confirm, F.data == "cancel_broadcast")
async def cancel_broadcast(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.answer("Bekor qilindi.")
    await callback.message.edit_text("❌ Reklama yuborish bekor qilindi.")
