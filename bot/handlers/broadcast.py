import json
import logging
import re

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from bot.database import Database
from bot.keyboards.admin import (
    broadcast_target_keyboard,
    confirm_post_keyboard,
    post_buttons_keyboard,
    post_media_keyboard,
    send_type_keyboard,
)
from bot.keyboards.user import admin_main_keyboard, back_keyboard
from bot.states import BroadcastStates, PostStates

router = Router()
logger = logging.getLogger(__name__)


def parse_inline_buttons(text: str) -> InlineKeyboardMarkup | None:
    """
    Format: Har bir qator — Tugma matni | URL yoki callback
    Masalan:
    Kanalga o'tish | https://t.me/channel
    Buyurtma | order_btn
    """
    rows = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if not line or "|" not in line:
            continue
        parts = [p.strip() for p in line.split("|", 1)]
        if len(parts) != 2:
            continue
        label, value = parts
        if value.startswith("http"):
            rows.append([InlineKeyboardButton(text=label, url=value)])
        else:
            rows.append(
                [InlineKeyboardButton(text=label, callback_data=value[:64])]
            )
    return InlineKeyboardMarkup(inline_keyboard=rows) if rows else None


async def send_post(
    bot: Bot,
    chat_id: int,
    text: str | None,
    media_type: str | None,
    file_id: str | None,
    buttons: InlineKeyboardMarkup | None,
) -> bool:
    try:
        if media_type == "photo" and file_id:
            await bot.send_photo(
                chat_id, file_id, caption=text, reply_markup=buttons
            )
        elif media_type == "video" and file_id:
            await bot.send_video(
                chat_id, file_id, caption=text, reply_markup=buttons
            )
        elif text:
            await bot.send_message(chat_id, text, reply_markup=buttons)
        else:
            return False
        return True
    except Exception as e:
        logger.error("Post yuborilmadi %s: %s", chat_id, e)
        return False


# ─── Xabar Yuborish ───────────────────────────────────────────────

@router.message(F.text == "📢 Xabar Yuborish")
async def broadcast_start(
    message: Message, state: FSMContext, db: Database, is_admin: bool
) -> None:
    if not is_admin:
        return
    await state.set_state(BroadcastStates.choosing_target)
    targets = await db.get_saved_targets()
    await message.answer(
        "📢 <b>Xabar yuborish</b>\n\nQayerga yubormoqchisiz?",
        reply_markup=send_type_keyboard(),
    )
    await state.update_data(targets=targets)


@router.callback_query(F.data == "send:cancel")
async def send_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if callback.message:
        await callback.message.edit_text("Bekor qilindi.")
        await callback.message.answer(
            "Admin panel", reply_markup=admin_main_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data.startswith("send:"))
async def send_type_chosen(
    callback: CallbackQuery, state: FSMContext, db: Database, is_admin: bool
) -> None:
    if not is_admin:
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    action = callback.data.split(":")[1]
    if action == "cancel":
        return

    if action == "user":
        await state.set_state(BroadcastStates.waiting_user_id)
        if callback.message:
            await callback.message.edit_text(
                "Foydalanuvchi Telegram ID sini yuboring:"
            )
        await callback.answer()
        return

    target_type = "channel" if action == "channel" else "group"
    await state.update_data(target_type=target_type)
    await state.set_state(BroadcastStates.choosing_target)

    targets = await db.get_saved_targets()
    filtered = [t for t in targets if t["type"] == target_type]

    if callback.message:
        await callback.message.edit_text(
            f"Saqlangan {'kanal' if target_type == 'channel' else 'guruh'}ni tanlang "
            "yoki yangisini qo'shing:",
            reply_markup=broadcast_target_keyboard(filtered),
        )
    await callback.answer()


@router.message(BroadcastStates.waiting_user_id)
async def broadcast_user_id(
    message: Message, state: FSMContext, is_admin: bool
) -> None:
    if not is_admin or not message.text or not message.text.strip().isdigit():
        await message.answer("To'g'ri ID yuboring.")
        return
    await state.update_data(
        target_chat_id=int(message.text.strip()), target_title="Foydalanuvchi"
    )
    await state.set_state(BroadcastStates.waiting_content)
    await message.answer(
        "Xabarni yuboring (matn, rasm yoki video).\n"
        "Inline tugmalar uchun keyin so'raladi.",
        reply_markup=back_keyboard(),
    )


@router.callback_query(F.data == "bc:add_target")
async def bc_add_target(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(BroadcastStates.waiting_new_target)
    if callback.message:
        await callback.message.edit_text(
            "Kanal yoki guruhga botni admin qiling, keyin "
            "kanal/guruh username yoki ID sini yuboring.\n"
            "Masalan: @FxDubbing yoki -100123456789"
        )
    await callback.answer()


@router.message(BroadcastStates.waiting_new_target)
async def bc_save_target(
    message: Message, state: FSMContext, bot: Bot, db: Database, is_admin: bool
) -> None:
    if not is_admin or not message.text:
        return

    raw = message.text.strip()
    data = await state.get_data()
    target_type = data.get("target_type", "channel")

    try:
        if raw.startswith("-") or raw.isdigit():
            chat_id = int(raw)
        else:
            chat_id = (await bot.get_chat(raw)).id
        chat = await bot.get_chat(chat_id)
        title = chat.title or chat.username or str(chat_id)
        saved = await db.add_saved_target(chat_id, title, target_type, message.from_user.id)
        if saved:
            await message.answer(f"✅ Saqlandi: <b>{title}</b>")
        else:
            await message.answer("Bu kanal/guruh allaqachon saqlangan.")
        await state.update_data(target_chat_id=chat_id, target_title=title)
        await state.set_state(BroadcastStates.waiting_content)
        await message.answer(
            "Endi xabarni yuboring (matn, rasm yoki video):",
            reply_markup=back_keyboard(),
        )
    except Exception as e:
        await message.answer(f"Xato: {e}\nBot admin ekanligini tekshiring.")


@router.callback_query(F.data.startswith("bc:target:"))
async def bc_target_selected(
    callback: CallbackQuery, state: FSMContext, db: Database, is_admin: bool
) -> None:
    if not is_admin:
        await callback.answer("Ruxsat yo'q!", show_alert=True)
        return

    target_id = int(callback.data.split(":")[2])
    target = await db.get_saved_target(target_id)
    if not target:
        await callback.answer("Topilmadi", show_alert=True)
        return

    await state.update_data(
        target_chat_id=target["chat_id"], target_title=target["title"]
    )
    await state.set_state(BroadcastStates.waiting_content)
    if callback.message:
        await callback.message.edit_text(
            f"✅ Tanlandi: <b>{target['title']}</b>\n\n"
            "Xabarni yuboring (matn, rasm yoki video):"
        )
    await callback.answer()


@router.message(BroadcastStates.waiting_content, F.text == "🔙 Ortga")
async def bc_content_back(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Bekor qilindi.", reply_markup=admin_main_keyboard())


@router.message(BroadcastStates.waiting_content)
async def bc_receive_content(
    message: Message, state: FSMContext, is_admin: bool
) -> None:
    if not is_admin:
        return

    media_type, file_id, text = None, None, None

    if message.photo:
        media_type, file_id = "photo", message.photo[-1].file_id
        text = message.caption
    elif message.video:
        media_type, file_id = "video", message.video.file_id
        text = message.caption
    elif message.text:
        text = message.html_text
    else:
        await message.answer("Matn, rasm yoki video yuboring.")
        return

    await state.update_data(media_type=media_type, file_id=file_id, text=text)
    await state.set_state(BroadcastStates.waiting_buttons)
    await message.answer(
        "Inline tugmalar qo'shasizmi?\n\n"
        "Format (har qator):\n"
        "<code>Tugma matni | https://link.com</code>\n\n"
        "Tugma kerak bo'lmasa <b>yo'q</b> deb yozing.",
        reply_markup=back_keyboard(),
    )


@router.message(BroadcastStates.waiting_buttons, F.text == "🔙 Ortga")
async def bc_buttons_back(message: Message, state: FSMContext) -> None:
    await state.set_state(BroadcastStates.waiting_content)
    await message.answer("Xabarni qayta yuboring:")


@router.message(BroadcastStates.waiting_buttons)
async def bc_send_final(
    message: Message, state: FSMContext, bot: Bot, is_admin: bool
) -> None:
    if not is_admin:
        return

    data = await state.get_data()
    chat_id = data.get("target_chat_id")
    if not chat_id:
        await message.answer("Maqsad tanlanmagan.")
        await state.clear()
        return

    buttons = None
    if message.text and message.text.strip().lower() != "yo'q":
        buttons = parse_inline_buttons(message.text)

    ok = await send_post(
        bot,
        chat_id,
        data.get("text"),
        data.get("media_type"),
        data.get("file_id"),
        buttons,
    )

    await state.clear()
    if ok:
        await message.answer(
            f"✅ Xabar yuborildi: {data.get('target_title', chat_id)}",
            reply_markup=admin_main_keyboard(),
        )
    else:
        await message.answer(
            "❌ Xabar yuborilmadi. Bot admin ekanligini tekshiring.",
            reply_markup=admin_main_keyboard(),
        )


# ─── Post Yaratish ────────────────────────────────────────────────

@router.message(F.text == "📝 Post Yaratish")
async def post_start(message: Message, state: FSMContext, is_admin: bool) -> None:
    if not is_admin:
        return
    await state.set_state(PostStates.choosing_media)
    await message.answer(
        "📝 <b>Post yaratish</b>\n\nMedia turini tanlang:",
        reply_markup=post_media_keyboard(),
    )


@router.callback_query(F.data == "post:cancel")
async def post_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    if callback.message:
        await callback.message.edit_text("Bekor qilindi.")
        await callback.message.answer(
            "Admin panel", reply_markup=admin_main_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data.startswith("post:media:"))
async def post_media_chosen(callback: CallbackQuery, state: FSMContext) -> None:
    media = callback.data.split(":")[2]
    await state.update_data(media_type=None if media == "none" else media, file_id=None)

    if media == "none":
        await state.set_state(PostStates.waiting_text)
        if callback.message:
            await callback.message.edit_text(
                "Post matnini yuboring (HTML format qo'llab-quvvatlanadi):"
            )
    else:
        await state.set_state(PostStates.waiting_media)
        if callback.message:
            await callback.message.edit_text(
                f"{'Rasm' if media == 'photo' else 'Video'} yuboring:"
            )
    await callback.answer()


@router.message(PostStates.waiting_media, F.photo | F.video)
async def post_receive_media(message: Message, state: FSMContext) -> None:
    if message.photo:
        await state.update_data(media_type="photo", file_id=message.photo[-1].file_id)
    elif message.video:
        await state.update_data(media_type="video", file_id=message.video.file_id)
    await state.set_state(PostStates.waiting_text)
    await message.answer(
        "Post matnini yuboring (caption). Bo'sh bo'lsa <b>-</b> deb yozing."
    )


@router.message(PostStates.waiting_text)
async def post_receive_text(message: Message, state: FSMContext) -> None:
    text = None if message.text and message.text.strip() == "-" else message.html_text
    await state.update_data(text=text)
    await state.set_state(PostStates.choosing_buttons)
    await message.answer(
        "Inline tugmalar qo'shasizmi?",
        reply_markup=post_buttons_keyboard(),
    )


@router.callback_query(F.data == "post:buttons:no")
async def post_no_buttons(callback: CallbackQuery, state: FSMContext, db: Database) -> None:
    await state.update_data(buttons_json=None)
    await _post_choose_target(callback, state, db)


@router.callback_query(F.data == "post:buttons:yes")
async def post_yes_buttons(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PostStates.waiting_buttons)
    if callback.message:
        await callback.message.edit_text(
            "Tugmalarni yuboring.\n"
            "Format:\n<code>Tugma | https://link.com</code>\n"
            "Har qator — bitta tugma."
        )
    await callback.answer()


@router.message(PostStates.waiting_buttons)
async def post_receive_buttons(
    message: Message, state: FSMContext, db: Database
) -> None:
    buttons = parse_inline_buttons(message.text or "")
    await state.update_data(buttons_json=buttons.model_dump() if buttons else None)
    await state.set_state(PostStates.choosing_target)
    targets = await db.get_saved_targets()
    await message.answer(
        "Qayerga yuborilsin?",
        reply_markup=broadcast_target_keyboard(targets),
    )


async def _post_choose_target(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    await state.set_state(PostStates.choosing_target)
    targets = await db.get_saved_targets()
    if callback.message:
        await callback.message.edit_text(
            "Qayerga yuborilsin?",
            reply_markup=broadcast_target_keyboard(targets),
        )
    await callback.answer()


@router.callback_query(PostStates.choosing_target, F.data == "bc:add_target")
async def post_add_target(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(PostStates.waiting_new_target)
    if callback.message:
        await callback.message.edit_text(
            "Kanal yoki guruh username/ID sini yuboring.\n"
            "Bot u yerda admin bo'lishi kerak."
        )
    await callback.answer()


@router.message(PostStates.waiting_new_target)
async def post_save_target(
    message: Message, state: FSMContext, bot: Bot, db: Database, is_admin: bool
) -> None:
    if not is_admin or not message.text:
        return

    raw = message.text.strip()
    try:
        if raw.startswith("-") or raw.isdigit():
            chat_id = int(raw)
        else:
            chat_id = (await bot.get_chat(raw)).id
        chat = await bot.get_chat(chat_id)
        title = chat.title or chat.username or str(chat_id)
        ttype = "channel" if chat.type == "channel" else "group"
        await db.add_saved_target(chat_id, title, ttype, message.from_user.id)
        await state.update_data(target_chat_id=chat_id, target_title=title)
        await state.set_state(PostStates.confirm)
        data = await state.get_data()
        await message.answer(
            f"✅ Saqlandi: <b>{title}</b>\n\n"
            f"🎯 Maqsad: {title}\n"
            f"📎 Media: {data.get('media_type') or 'yoq'}\n"
            f"📝 Matn: {data.get('text') or '—'}",
            reply_markup=confirm_post_keyboard(),
        )
    except Exception as e:
        await message.answer(f"Xato: {e}")


@router.callback_query(PostStates.choosing_target, F.data.startswith("bc:target:"))
async def post_target_selected(
    callback: CallbackQuery, state: FSMContext, db: Database
) -> None:
    target_id = int(callback.data.split(":")[2])
    target = await db.get_saved_target(target_id)
    if not target:
        await callback.answer("Topilmadi", show_alert=True)
        return

    await state.update_data(
        target_chat_id=target["chat_id"], target_title=target["title"]
    )
    await state.set_state(PostStates.confirm)

    data = await state.get_data()
    preview = (
        f"📋 <b>Post ko'rinishi</b>\n\n"
        f"🎯 Maqsad: {target['title']}\n"
        f"📎 Media: {data.get('media_type') or 'yoq'}\n"
        f"📝 Matn: {data.get('text') or '—'}"
    )
    if callback.message:
        await callback.message.edit_text(
            preview, reply_markup=confirm_post_keyboard()
        )
    await callback.answer()


@router.callback_query(F.data == "post:confirm:send")
async def post_confirm_send(
    callback: CallbackQuery, state: FSMContext, bot: Bot
) -> None:
    data = await state.get_data()
    buttons = None
    if data.get("buttons_json"):
        buttons = InlineKeyboardMarkup.model_validate(data["buttons_json"])

    ok = await send_post(
        bot,
        data["target_chat_id"],
        data.get("text"),
        data.get("media_type"),
        data.get("file_id"),
        buttons,
    )

    await state.clear()
    if callback.message:
        if ok:
            await callback.message.edit_text(
                f"✅ Post yuborildi: {data.get('target_title')}"
            )
        else:
            await callback.message.edit_text("❌ Post yuborilmadi.")
        await callback.message.answer(
            "Admin panel", reply_markup=admin_main_keyboard()
        )
    await callback.answer()
