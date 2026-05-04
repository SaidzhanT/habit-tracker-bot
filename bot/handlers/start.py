from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from db import queries

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    user = message.from_user
    await queries.upsert_user(user.id, user.username)
    await message.answer(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я помогу тебе отслеживать привычки.\n\n"
        "Команды:\n"
        "/add — добавить привычку\n"
        "/habits — список привычек\n"
        "/categories — управление категориями\n"
        "/checkin — отметить сегодня\n"
        "/stats — статистика\n"
        "/settings — настройки напоминания"
    )
