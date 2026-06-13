import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import Config
from bot.database import Database
from bot.handlers import admin_panel, broadcast, payment, user
from bot.middlewares.admin import AdminMiddleware
from bot.middlewares.database import DatabaseMiddleware
from bot.services.scheduler import setup_scheduler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)


async def main() -> None:
    config = Config.from_env()
    db = Database(config)
    await db.init()

    bot = Bot(
        token=config.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher(storage=MemoryStorage())

    dp["db"] = db
    dp["config"] = config

    db_mw = DatabaseMiddleware(db, config)
    admin_mw = AdminMiddleware(db)
    for observer in (dp.message, dp.callback_query, dp.edited_message):
        observer.middleware(db_mw)
        observer.middleware(admin_mw)

    dp.include_router(user.router)
    dp.include_router(payment.router)
    dp.include_router(admin_panel.router)
    dp.include_router(broadcast.router)

    scheduler = setup_scheduler(bot, db, config)
    scheduler.start()

    logger.info("X-Dubbing Bot ishga tushdi...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
