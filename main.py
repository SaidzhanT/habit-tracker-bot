import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from scheduler import setup_scheduler
from bot.handlers import start, habits, categories, checkin, stats, settings as settings_handler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


async def main() -> None:
    bot = Bot(token=settings.telegram_bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(start.router)
    dp.include_router(habits.router)
    dp.include_router(categories.router)
    dp.include_router(checkin.router)
    dp.include_router(stats.router)
    dp.include_router(settings_handler.router)

    scheduler = setup_scheduler(bot)
    scheduler.start()

    logging.info("Bot started")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
