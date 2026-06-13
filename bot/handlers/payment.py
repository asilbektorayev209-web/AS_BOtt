import logging
from datetime import datetime

from aiogram import Bot, Router, F
from aiogram.types import CallbackQuery, Message

from bot.config import SUBSCRIPTION_DAYS, SUBSCRIPTION_LABELS, Config
from bot.database import Database
from bot.keyboards.admin import payment_approval_keyboard
from bot.services.subscription import approve_user_in_group, kick_user_from_group
from bot.texts import (
    payment_admin_text,
    subscription_approved_text,
    subscription_rejected_text,
)

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.photo)
async def receive_payment_photo(
    message: Message,
    bot: Bot,
    db: Database,
    config: Config,
    is_admin: bool,
) -> None:
    if not message.from_user or not message.photo:
        return

    # Admin panelda rasm yuborilganda to'lov sifatida qabul qilinmasin
    if is_admin:
        return

    user = message.from_user
    if await db.has_pending_payment(user.id):
        await message.answer(
            "⏳ Sizda allaqachon ko'rib chiqilayotgan chek bor. "
            "Iltimos, javobni kuting."
        )
        return

    file_id = message.photo[-1].file_id
    transaction_id, _ = await db.create_payment(user.id, file_id)

    created_at = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    admin_text = payment_admin_text(
        transaction_id,
        user.full_name,
        user.username,
        user.id,
        created_at,
    )

    admins = await db.get_admins()
    for admin in admins:
        try:
            await bot.send_photo(
                admin["user_id"],
                photo=file_id,
                caption=admin_text,
                reply_markup=payment_approval_keyboard(transaction_id),
            )
        except Exception as e:
            logger.warning("Admin %s ga xabar yuborilmadi: %s", admin["user_id"], e)

    await message.answer(
        "✅ Chekingiz qabul qilindi!\n"
        "Adminlar tekshiradi. Odatda 5-15 daqiqada javob beriladi."
    )


@router.callback_query(F.data.startswith("pay:approve:"))
async def approve_payment(
    callback: CallbackQuery, bot: Bot, db: Database, config: Config, is_admin: bool
) -> None:
    if not is_admin:
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) != 4:
        await callback.answer("Xato ma'lumot", show_alert=True)
        return

    transaction_id, plan = parts[2], parts[3]
    days = SUBSCRIPTION_DAYS.get(plan)
    if not days:
        await callback.answer("Noto'g'ri reja", show_alert=True)
        return

    payment = await db.approve_payment(
        transaction_id, callback.from_user.id, plan, days
    )
    if not payment:
        await callback.answer("Bu chek allaqachon qayta ishlangan!", show_alert=True)
        return

    user_id = payment["user_id"]
    plan_label = SUBSCRIPTION_LABELS[plan]

    # Guruhga qo'shish
    joined = await approve_user_in_group(bot, config.private_group_id, user_id)
    if not joined:
        # Join request bo'lmasa, foydalanuvchini xabardor qilish
        logger.warning("User %s guruhga qo'shilmadi", user_id)

    try:
        await bot.send_message(
            user_id,
            subscription_approved_text(plan_label),
        )
    except Exception as e:
        logger.warning("User %s ga xabar yuborilmadi: %s", user_id, e)

    if callback.message:
        await callback.message.edit_caption(
            caption=(
                callback.message.caption or ""
            )
            + f"\n\n✅ <b>Tasdiqlandi:</b> {plan_label} — {callback.from_user.full_name}",
        )

    await callback.answer(f"Tasdiqlandi: {plan_label}")


@router.callback_query(F.data.startswith("pay:reject:"))
async def reject_payment(
    callback: CallbackQuery, bot: Bot, db: Database, is_admin: bool
) -> None:
    if not is_admin:
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    transaction_id = callback.data.split(":")[2]
    reason = "Soxta chek"

    payment = await db.reject_payment(
        transaction_id, callback.from_user.id, reason
    )
    if not payment:
        await callback.answer("Bu chek allaqachon qayta ishlangan!", show_alert=True)
        return

    try:
        await bot.send_message(
            payment["user_id"],
            subscription_rejected_text(),
        )
    except Exception as e:
        logger.warning("Rad xabari yuborilmadi: %s", e)

    if callback.message:
        await callback.message.edit_caption(
            caption=(
                callback.message.caption or ""
            )
            + f"\n\n❌ <b>Rad etildi</b> — {callback.from_user.full_name}\n"
            f"Sabab: {reason}",
        )

    await callback.answer("Rad etildi")
