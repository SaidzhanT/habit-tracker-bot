from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def habit_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да/Нет", callback_data="htype:boolean")
    builder.button(text="🔢 Счётчик", callback_data="htype:counter")
    builder.adjust(2)
    return builder.as_markup()


def categories_kb(categories: list[dict], with_new: bool = True, with_none: bool = True) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=f"{cat['emoji']} {cat['name']}",
            callback_data=f"cat:{cat['id']}",
        )
    if with_new:
        builder.button(text="➕ Новая категория", callback_data="cat:new")
    if with_none:
        builder.button(text="⬜ Без категории", callback_data="cat:none")
    builder.adjust(2)
    return builder.as_markup()


def checkin_kb(habits: list[dict], logs: dict[str, dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for habit in habits:
        log = logs.get(habit["id"])
        is_done = log and log["is_done"]
        value = log["value"] if log else 0
        target = habit.get("target_value")
        unit = habit.get("unit", "")

        if habit["type"] == "boolean":
            icon = "✅" if is_done else "⬜"
            label = f"{icon} {habit['name']}"
        else:
            goal_reached = target and value >= target
            icon = "🔥" if goal_reached else ("🔢" if value > 0 else "⬜")
            label = f"{icon} {habit['name']}: {value}"
            if target:
                label += f"/{target}"
            if unit:
                label += f" {unit}"

        builder.button(text=label, callback_data=f"ci:{habit['id']}:{habit['type']}")
    builder.button(text="✔️ Готово", callback_data="ci:done")
    builder.adjust(1)
    return builder.as_markup()


def habits_list_kb(habits: list[dict], action: str = "del") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for habit in habits:
        cat = habit.get("categories") or {}
        cat_str = f" [{cat.get('emoji','')}{cat.get('name','')}]" if cat else ""
        builder.button(
            text=f"🗑 {habit['name']}{cat_str}",
            callback_data=f"{action}:{habit['id']}",
        )
    builder.adjust(1)
    return builder.as_markup()


def categories_manage_kb(categories: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(
            text=f"🗑 {cat['emoji']} {cat['name']}",
            callback_data=f"delcat:{cat['id']}",
        )
    builder.button(text="➕ Добавить", callback_data="delcat:new")
    builder.adjust(1)
    return builder.as_markup()


def confirm_kb(yes_data: str, no_data: str = "cancel") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Да", callback_data=yes_data)
    builder.button(text="❌ Отмена", callback_data=no_data)
    builder.adjust(2)
    return builder.as_markup()
