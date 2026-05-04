from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards import checkin_kb
from bot.states import CounterInput
from db import queries

router = Router()


async def _send_checkin(message: Message, user_id: int, edit: bool = False) -> None:
    habits = await queries.get_habits(user_id)
    if not habits:
        await message.answer("Привычек нет. Добавь через /add")
        return

    logs = await queries.get_today_logs(user_id)
    text = "📋 Отметь привычки за сегодня:"
    kb = checkin_kb(habits, logs)

    if edit:
        await message.edit_text(text, reply_markup=kb)
    else:
        await message.answer(text, reply_markup=kb)


@router.message(Command("checkin"))
async def cmd_checkin(message: Message) -> None:
    await _send_checkin(message, message.from_user.id)


@router.callback_query(F.data.startswith("ci:") & ~F.data.endswith(":done"))
async def checkin_toggle(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    habit_id, habit_type = parts[1], parts[2]

    if habit_type == "boolean":
        await queries.toggle_boolean_log(habit_id)
        habits = await queries.get_habits(callback.from_user.id)
        logs = await queries.get_today_logs(callback.from_user.id)
        await callback.message.edit_reply_markup(reply_markup=checkin_kb(habits, logs))
        await callback.answer()
    else:
        await state.set_state(CounterInput.value)
        await state.update_data(habit_id=habit_id, checkin_message_id=callback.message.message_id)
        await callback.message.answer("Введи значение (число):")
        await callback.answer()


@router.message(CounterInput.value)
async def counter_value_input(message: Message, state: FSMContext) -> None:
    if not message.text.isdigit():
        await message.answer("Введи целое число:")
        return

    data = await state.get_data()
    habit_id = data["habit_id"]
    await queries.set_counter_log(habit_id, int(message.text))
    await state.clear()
    await message.answer("✅ Записано!")

    habits = await queries.get_habits(message.from_user.id)
    logs = await queries.get_today_logs(message.from_user.id)
    await message.answer("📋 Отметь привычки за сегодня:", reply_markup=checkin_kb(habits, logs))


@router.callback_query(F.data == "ci:done")
async def checkin_done(callback: CallbackQuery) -> None:
    logs = await queries.get_today_logs(callback.from_user.id)
    done = sum(1 for l in logs.values() if l["is_done"])
    total = len(await queries.get_habits(callback.from_user.id))
    await callback.message.edit_text(f"🎉 Чекин завершён! Выполнено {done}/{total} привычек.")
    await callback.answer()
