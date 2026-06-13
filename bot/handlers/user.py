from datetime import datetime

from aiogram import Bot, Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.config import Config
from bot.database import Database
from bot.keyboards.user import admin_entry_keyboard, user_main_keyboard
from bot.texts import premium_info_text, support_text

router = Router()


def _user_display(message: Message) -> tuple[str, str | None]:
    user = message.from_user
    name = user.full_name if user else "Noma'lum"
    username = user.username if user else None
    return name, username


@router.message(CommandStart())
async def cmd_start(
    message: Message, db: Database, config: Config, is_admin: bool
) -> None:
    if not message.from_user:
        return

    name, username = _user_display(message)
    await db.ensure_user(message.from_user.id, username, name)

    text = (
        f"Assalomu alaykum, <b>{name}</b>! 👋\n\n"
        "X-Dubbing Premium botiga xush kelibsiz.\n"
        "Quyidagi tugmalardan birini tanlang:"
    )

    if is_admin:
        await message.answer(
            text + "\n\n⚙️ Admin panel uchun pastdagi tugmani bosing:",
            reply_markup=admin_entry_keyboard(),
        )
        await message.answer(
            "Foydalanuvchi menyusi:",
            reply_markup=user_main_keyboard(),
        )
    else:
        await message.answer(text, reply_markup=user_main_keyboard())


@router.message(F.text == "💎 Premium Obuna olish")
async def premium_info(message: Message, config: Config) -> None:
    text = premium_info_text(
        config.payment_card, config.payment_name, config.channel_link
    )
    await message.answer(text, disable_web_page_preview=False)


@router.message(F.text == "📞 Aloqa uchun")
async def contact_support(message: Message, config: Config) -> None:
    await message.answer(
        support_text(config.support_username, config.support_phone)
    )


@router.message(F.text == "⚙️ Admin Panel")
async def admin_panel(message: Message, is_admin: bool) -> None:
    if not is_admin:
        await message.answer("❌ Sizda admin huquqi yo'q.")
        return
    from bot.keyboards.user import admin_main_keyboard

    await message.answer(
        "⚙️ <b>Admin Panel</b>\n\nKerakli bo'limni tanlang:",
        reply_markup=admin_main_keyboard(),
    )
    await message.answer(
        "Foydalanuvchi menyusi:",
        reply_markup=user_main_keyboard(),
    )


@router.message(F.text == "🔙 Ortga")
async def go_back(message: Message, is_admin: bool) -> None:
    text = "Asosiy menyu:"
    markup = user_main_keyboard()
    if is_admin:
        markup = admin_entry_keyboard()
        await message.answer(text, reply_markup=markup)
        await message.answer(
            "Foydalanuvchi menyusi:",
            reply_markup=user_main_keyboard(),
        )
    else:
        await message.answer(text, reply_markup=markup)
