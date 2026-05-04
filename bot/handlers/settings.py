import re
from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.states import SetReminder
from db import queries

router = Router()

TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


@router.message(Command("settings"))
async def cmd_settings(message: Message) -> None:
    user = await queries.get_user(message.from_user.id)
    reminder = user["reminder_time"][:5] if user else "20:00"
    await message.answer(
        f"⚙️ Настройки\n\n"
        f"🔔 Время напоминания: {reminder}\n\n"
        "Чтобы изменить, отправь /settime ЧЧ:ММ\n"
        "Например: /settime 21:30"
    )


@router.message(Command("settime"))
async def cmd_settime(message: Message) -> None:
    parts = message.text.strip().split()
    if len(parts) == 2 and TIME_RE.match(parts[1]):
        await queries.update_reminder_time(message.from_user.id, parts[1])
        await message.answer(f"✅ Напоминание установлено на {parts[1]}")
    else:
        await message.answer("Формат: /settime ЧЧ:ММ  (например: /settime 21:00)")
