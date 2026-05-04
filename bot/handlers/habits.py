from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards import habit_type_kb, categories_kb, habits_list_kb, confirm_kb
from bot.states import AddHabit
from db import queries

router = Router()


# ── /habits ──────────────────────────────────────────────────────────────────

@router.message(Command("habits"))
async def cmd_habits(message: Message) -> None:
    habits = await queries.get_habits(message.from_user.id)
    if not habits:
        await message.answer("У тебя ещё нет привычек. Добавь через /add")
        return

    lines = []
    for h in habits:
        cat = h.get("categories") or {}
        cat_str = f"  [{cat.get('emoji','')}{cat.get('name','')}]" if cat else ""
        t = "✅" if h["type"] == "boolean" else f"🔢 (цель: {h['target_value']} {h['unit'] or ''})"
        lines.append(f"• {h['name']}{cat_str} — {t}")

    await message.answer("📋 Твои привычки:\n\n" + "\n".join(lines))


# ── /add ─────────────────────────────────────────────────────────────────────

@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext) -> None:
    await state.set_state(AddHabit.name)
    await message.answer("Как называется привычка? Напиши название:")


@router.message(AddHabit.name)
async def add_habit_name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=message.text.strip())
    await state.set_state(AddHabit.habit_type)
    await message.answer("Какой тип привычки?", reply_markup=habit_type_kb())


@router.callback_query(AddHabit.habit_type, F.data.startswith("htype:"))
async def add_habit_type(callback: CallbackQuery, state: FSMContext) -> None:
    habit_type = callback.data.split(":")[1]
    await state.update_data(habit_type=habit_type)
    await callback.message.edit_reply_markup()

    if habit_type == "counter":
        await state.set_state(AddHabit.counter_target)
        await callback.message.answer("Укажи цель (число). Например: 8, 5, 30")
    else:
        await _ask_category(callback.message, state, callback.from_user.id)


@router.message(AddHabit.counter_target)
async def add_habit_target(message: Message, state: FSMContext) -> None:
    if not message.text.isdigit():
        await message.answer("Введи число, например: 8")
        return
    await state.update_data(target_value=int(message.text))
    await state.set_state(AddHabit.counter_unit)
    await message.answer("Единица измерения (напр: стаканов, км, мин). Или отправь /skip")


@router.message(AddHabit.counter_unit)
async def add_habit_unit(message: Message, state: FSMContext) -> None:
    unit = None if message.text == "/skip" else message.text.strip()
    await state.update_data(unit=unit)
    await _ask_category(message, state, message.from_user.id)


async def _ask_category(message: Message, state: FSMContext, user_id: int) -> None:
    categories = await queries.get_categories(user_id)
    await state.set_state(AddHabit.category)
    await message.answer("Выбери категорию:", reply_markup=categories_kb(categories))


@router.callback_query(AddHabit.category, F.data.startswith("cat:"))
async def add_habit_category(callback: CallbackQuery, state: FSMContext) -> None:
    val = callback.data.split(":", 1)[1]
    user_id = callback.from_user.id

    if val == "new":
        await callback.message.edit_reply_markup()
        await callback.message.answer("Введи название новой категории (можно с эмодзи, напр: 💧 Здоровье):")
        await state.update_data(creating_category=True)
        return

    category_id = None if val == "none" else val
    await _finish_add(callback.message, state, user_id, category_id)
    await callback.message.edit_reply_markup()


@router.message(AddHabit.category)
async def add_habit_new_category(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    if not data.get("creating_category"):
        return

    text = message.text.strip()
    parts = text.split(maxsplit=1)
    if len(parts) == 2 and len(parts[0]) <= 2:
        emoji, name = parts[0], parts[1]
    else:
        emoji, name = "📌", text

    cat = await queries.create_category(message.from_user.id, name, emoji)
    await _finish_add(message, state, message.from_user.id, cat["id"])


async def _finish_add(message: Message, state: FSMContext, user_id: int, category_id: str | None) -> None:
    data = await state.get_data()
    await queries.create_habit(
        user_id=user_id,
        name=data["name"],
        habit_type=data["habit_type"],
        category_id=category_id,
        target_value=data.get("target_value"),
        unit=data.get("unit"),
    )
    await state.clear()
    await message.answer(f"✅ Привычка «{data['name']}» добавлена! Отмечай её через /checkin")


# ── /delete ───────────────────────────────────────────────────────────────────

@router.message(Command("delete"))
async def cmd_delete(message: Message) -> None:
    habits = await queries.get_habits(message.from_user.id)
    if not habits:
        await message.answer("Нечего удалять — привычек нет.")
        return
    await message.answer("Какую привычку удалить?", reply_markup=habits_list_kb(habits, action="del"))


@router.callback_query(F.data.startswith("del:"))
async def delete_habit_confirm(callback: CallbackQuery) -> None:
    habit_id = callback.data.split(":", 1)[1]
    habit = await queries.get_habit(habit_id, callback.from_user.id)
    if not habit:
        await callback.answer("Привычка не найдена", show_alert=True)
        return
    await callback.message.edit_text(
        f"Удалить привычку «{habit['name']}»? Логи сохранятся.",
        reply_markup=confirm_kb(f"delconfirm:{habit_id}"),
    )


@router.callback_query(F.data.startswith("delconfirm:"))
async def delete_habit_do(callback: CallbackQuery) -> None:
    habit_id = callback.data.split(":", 1)[1]
    await queries.deactivate_habit(habit_id, callback.from_user.id)
    await callback.message.edit_text("🗑 Привычка архивирована.")


@router.callback_query(F.data == "cancel")
async def cancel_cb(callback: CallbackQuery) -> None:
    await callback.message.edit_text("Отменено.")
