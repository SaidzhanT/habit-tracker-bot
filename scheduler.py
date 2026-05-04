from datetime import datetime, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram import Bot
from db import queries


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone="UTC")
    scheduler.add_job(
        send_reminders,
        trigger="cron",
        minute="*",
        args=[bot],
        id="reminders",
        replace_existing=True,
    )
    return scheduler


async def send_reminders(bot: Bot) -> None:
    now = datetime.now(timezone.utc)
    current_time = now.strftime("%H:%M")
    users = await queries.get_all_users_for_reminder(current_time)
    for user in users:
        try:
            await bot.send_message(
                user["telegram_id"],
                "⏰ Вечерний чекин!\nНе забудь отметить привычки → /checkin",
            )
        except Exception:
            pass
