import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.config import Config
from bot.database import Database
from bot.services.subscription import kick_user_from_group

logger = logging.getLogger(__name__)


async def check_expired_subscriptions(bot: Bot, db: Database, config: Config) -> None:
    expired = await db.get_expired_subscriptions()
    for sub in expired:
        user_id = sub["user_id"]
        kicked = await kick_user_from_group(bot, config.private_group_id, user_id)
        await db.expire_subscription(sub["id"])

        if kicked:
            try:
                await bot.send_message(
                    user_id,
                    "⏰ <b>Obunangiz muddati tugadi.</b>\n\n"
                    "Qayta obuna bo'lish uchun yangi chek yuboring.",
                )
            except Exception:
                pass

        logger.info("Subscription expired for user %s", user_id)


def setup_scheduler(bot: Bot, db: Database, config: Config) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        check_expired_subscriptions,
        "interval",
        hours=1,
        args=[bot, db, config],
        id="check_subscriptions",
        replace_existing=True,
    )
    return scheduler
