from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup


def user_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="💎 Premium Obuna olish")],
            [KeyboardButton(text="📞 Aloqa uchun")],
        ],
        resize_keyboard=True,
    )


def admin_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="📊 Statistika"),
                KeyboardButton(text="👥 Foydalanuvchilar"),
            ],
            [
                KeyboardButton(text="📢 Xabar Yuborish"),
                KeyboardButton(text="📝 Post Yaratish"),
            ],
            [
                KeyboardButton(text="Admin Qo'shish"),
                KeyboardButton(text="Admin O'chirish"),
            ],
            [KeyboardButton(text="📋 Adminlar Ro'yxati")],
            [KeyboardButton(text="🔙 Ortga")],
        ],
        resize_keyboard=True,
    )


def admin_entry_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="⚙️ Admin Panel")],
        ],
        resize_keyboard=True,
    )


def back_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🔙 Ortga")]],
        resize_keyboard=True,
    )
