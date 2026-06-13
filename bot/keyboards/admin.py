from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.config import SUBSCRIPTION_LABELS


def payment_approval_keyboard(transaction_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"✅ {SUBSCRIPTION_LABELS['1m']}",
                    callback_data=f"pay:approve:{transaction_id}:1m",
                ),
                InlineKeyboardButton(
                    text=f"✅ {SUBSCRIPTION_LABELS['3m']}",
                    callback_data=f"pay:approve:{transaction_id}:3m",
                ),
            ],
            [
                InlineKeyboardButton(
                    text=f"✅ {SUBSCRIPTION_LABELS['6m']}",
                    callback_data=f"pay:approve:{transaction_id}:6m",
                ),
                InlineKeyboardButton(
                    text=f"✅ {SUBSCRIPTION_LABELS['12m']}",
                    callback_data=f"pay:approve:{transaction_id}:12m",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="❌ Rad qilish",
                    callback_data=f"pay:reject:{transaction_id}",
                )
            ],
        ]
    )


def broadcast_target_keyboard(targets: list[dict]) -> InlineKeyboardMarkup:
    rows = [
        [
            InlineKeyboardButton(
                text="➕ Yangi Kanal/Guruh qo'shish",
                callback_data="bc:add_target",
            )
        ]
    ]
    for t in targets:
        icon = "📢" if t["type"] == "channel" else "👥"
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"{icon} {t['title']}",
                    callback_data=f"bc:target:{t['id']}",
                )
            ]
        )
    rows.append(
        [InlineKeyboardButton(text="🔙 Bekor", callback_data="bc:cancel")]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def send_type_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📢 Kanalga", callback_data="send:channel"
                ),
                InlineKeyboardButton(
                    text="👥 Guruhga", callback_data="send:group"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="👤 Foydalanuvchiga", callback_data="send:user"
                )
            ],
            [InlineKeyboardButton(text="🔙 Bekor", callback_data="send:cancel")],
        ]
    )


def post_media_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🖼 Rasm bilan", callback_data="post:media:photo"
                ),
                InlineKeyboardButton(
                    text="🎬 Video bilan", callback_data="post:media:video"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="📝 Faqat matn", callback_data="post:media:none"
                )
            ],
            [InlineKeyboardButton(text="🔙 Bekor", callback_data="post:cancel")],
        ]
    )


def post_buttons_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔗 Tugmalar qo'shish", callback_data="post:buttons:yes"
                ),
                InlineKeyboardButton(
                    text="⏭ Tugmasiz", callback_data="post:buttons:no"
                ),
            ],
            [InlineKeyboardButton(text="🔙 Bekor", callback_data="post:cancel")],
        ]
    )


def confirm_post_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Yuborish", callback_data="post:confirm:send"
                ),
                InlineKeyboardButton(
                    text="❌ Bekor", callback_data="post:cancel"
                ),
            ]
        ]
    )


def users_pagination_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    buttons = []
    if page > 0:
        buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"users:page:{page - 1}")
        )
    buttons.append(
        InlineKeyboardButton(
            text=f"{page + 1}/{total_pages}", callback_data="users:noop"
        )
    )
    if page < total_pages - 1:
        buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"users:page:{page + 1}")
        )
    return InlineKeyboardMarkup(inline_keyboard=[buttons])
