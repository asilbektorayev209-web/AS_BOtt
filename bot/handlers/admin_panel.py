import json
import logging
import re
from datetime import datetime

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.database import Database
from bot.keyboards.admin import users_pagination_keyboard
from bot.keyboards.user import admin_main_keyboard, back_keyboard
from bot.states import AdminManageStates

router = Router()
logger = logging.getLogger(__name__)

USERS_PER_PAGE = 8


@router.message(F.text == "📊 Statistika")
async def show_stats(message: Message, db: Database, is_admin: bool) -> None:
    if not is_admin:
        return
    stats = await db.get_stats()
    text = (
        "📊 <b>Statistika</b>\n\n"
        f"👥 Foydalanuvchilar: <b>{stats['users']}</b>\n"
        f"💎 Faol obunalar: <b>{stats['active_subs']}</b>\n"
        f"⏳ Kutilayotgan cheklar: <b>{stats['pending_payments']}</b>\n"
        f"✅ Tasdiqlangan: <b>{stats['approved_payments']}</b>\n"
        f"❌ Rad etilgan: <b>{stats['rejected_payments']}</b>\n"
        f"👑 Adminlar: <b>{stats['admins']}</b>"
    )
    await message.answer(text)


@router.message(F.text == "👥 Foydalanuvchilar")
async def show_users(message: Message, db: Database, is_admin: bool) -> None:
    if not is_admin:
        return
    await _send_users_page(message, db, 0)


async def _send_users_page(message: Message, db: Database, page: int) -> None:
    total = await db.count_users()
    total_pages = max(1, (total + USERS_PER_PAGE - 1) // USERS_PER_PAGE)
    page = min(page, total_pages - 1)
    users = await db.get_users_page(page * USERS_PER_PAGE, USERS_PER_PAGE)

    if not users:
        await message.answer("Hozircha foydalanuvchilar yo'q.")
        return

    lines = [f"👥 <b>Foydalanuvchilar</b> ({page + 1}/{total_pages})\n"]
    for u in users:
        uname = f"@{u['username']}" if u.get("username") else "—"
        exp = u.get("expires_at")
        exp_text = ""
        if exp:
            try:
                dt = datetime.fromisoformat(exp)
                exp_text = f" | ⏰ {dt.strftime('%d.%m.%Y')}"
            except ValueError:
                pass
        lines.append(
            f"• {u['full_name']} ({uname}) — <code>{u['user_id']}</code>{exp_text}"
        )

    await message.answer(
        "\n".join(lines),
        reply_markup=users_pagination_keyboard(page, total_pages),
    )


@router.callback_query(F.data.startswith("users:page:"))
async def users_page_callback(
    callback: CallbackQuery, db: Database, is_admin: bool
) -> None:
    if not is_admin:
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return
    page = int(callback.data.split(":")[2])
    if callback.message:
        await callback.message.delete()
        await _send_users_page(callback.message, db, page)
    await callback.answer()


@router.callback_query(F.data == "users:noop")
async def users_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.message(F.text == "📋 Adminlar Ro'yxati")
async def list_admins(message: Message, db: Database, is_admin: bool) -> None:
    if not is_admin:
        return
    admins = await db.get_admins()
    lines = ["📋 <b>Adminlar ro'yxati</b>\n"]
    for a in admins:
        uname = f"@{a['username']}" if a.get("username") else "—"
        name = a.get("full_name") or "Noma'lum"
        lines.append(f"• {name} ({uname}) — <code>{a['user_id']}</code>")
    await message.answer("\n".join(lines))


@router.message(F.text == "Admin Qo'shish")
async def admin_add_start(
    message: Message, state: FSMContext, is_admin: bool
) -> None:
    if not is_admin:
        return
    await state.set_state(AdminManageStates.waiting_add_id)
    await message.answer(
        "Yangi admin Telegram ID sini yuboring:\n"
        "(Foydalanuvchi ID sini @userinfobot orqali olish mumkin)",
        reply_markup=back_keyboard(),
    )


@router.message(AdminManageStates.waiting_add_id, F.text == "🔙 Ortga")
async def admin_add_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_main_keyboard())


@router.message(AdminManageStates.waiting_add_id)
async def admin_add_process(
    message: Message, state: FSMContext, bot: Bot, db: Database
) -> None:
    if not message.text or not message.text.strip().isdigit():
        await message.answer("Iltimos, faqat raqamli ID yuboring.")
        return

    user_id = int(message.text.strip())
    try:
        chat = await bot.get_chat(user_id)
        added = await db.add_admin(user_id, chat.username, chat.full_name or "Admin")
    except Exception:
        added = await db.add_admin(user_id, None, f"User {user_id}")

    await state.clear()
    if added:
        await message.answer(
            f"✅ Admin qo'shildi: <code>{user_id}</code>",
            reply_markup=admin_main_keyboard(),
        )
        try:
            await bot.send_message(
                user_id,
                "🎉 Siz X-Dubbing bot admini qilib tayinlandingiz!\n"
                "/start ni bosing.",
            )
        except Exception:
            pass
    else:
        await message.answer(
            "Bu foydalanuvchi allaqachon admin.",
            reply_markup=admin_main_keyboard(),
        )


@router.message(F.text == "Admin O'chirish")
async def admin_remove_start(
    message: Message, state: FSMContext, is_admin: bool
) -> None:
    if not is_admin:
        return
    await state.set_state(AdminManageStates.waiting_remove_id)
    await message.answer(
        "O'chiriladigan admin ID sini yuboring:",
        reply_markup=back_keyboard(),
    )


@router.message(AdminManageStates.waiting_remove_id, F.text == "🔙 Ortga")
async def admin_remove_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_main_keyboard())


@router.message(AdminManageStates.waiting_remove_id)
async def admin_remove_process(
    message: Message, state: FSMContext, db: Database
) -> None:
    if not message.text or not message.text.strip().isdigit():
        await message.answer("Iltimos, faqat raqamli ID yuboring.")
        return

    user_id = int(message.text.strip())
    removed = await db.remove_admin(user_id)
    await state.clear()

    if removed:
        await message.answer(
            f"✅ Admin o'chirildi: <code>{user_id}</code>",
            reply_markup=admin_main_keyboard(),
        )
    else:
        await message.answer(
            "Admin topilmadi yoki asosiy adminni o'chirib bo'lmaydi.",
            reply_markup=admin_main_keyboard(),
        )
