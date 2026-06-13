import logging

from aiogram import Bot

logger = logging.getLogger(__name__)


async def approve_user_in_group(bot: Bot, group_id: int, user_id: int) -> bool:
    """Foydalanuvchini yopiq guruhga qo'shish (join request orqali)."""
    try:
        await bot.approve_chat_join_request(chat_id=group_id, user_id=user_id)
        logger.info("User %s join request tasdiqlandi", user_id)
        return True
    except Exception as e:
        logger.warning("Join request tasdiqlanmadi (%s): %s", user_id, e)

    # Agar join request bo'lmasa, cheklovni olib tashlashga harakat
    try:
        await bot.unban_chat_member(
            chat_id=group_id, user_id=user_id, only_if_banned=True
        )
        return True
    except Exception as e:
        logger.warning("Unban muvaffaqiyatsiz (%s): %s", user_id, e)

    return False


async def kick_user_from_group(bot: Bot, group_id: int, user_id: int) -> bool:
    """Foydalanuvchini guruhdan chiqarish (bloklamasdan)."""
    try:
        await bot.ban_chat_member(chat_id=group_id, user_id=user_id)
        await bot.unban_chat_member(chat_id=group_id, user_id=user_id)
        logger.info("User %s guruhdan chiqarildi", user_id)
        return True
    except Exception as e:
        logger.warning("Kick muvaffaqiyatsiz (%s): %s", user_id, e)
        return False
