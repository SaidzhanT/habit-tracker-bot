from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from bot.keyboards import categories_manage_kb
from bot.states import AddCategory
from db import queries

router = Router()


@router.message(Command("categories"))
async def cmd_categories(message: Message) -> None:
    cats = await queries.get_categories(message.from_user.id)
    if not cats:
        await message.answer(
            "Категорий пока нет.\nНажми «Добавить» чтобы создать.",
            reply_markup=categories_manage_kb([]),
        )
    else:
        await message.answer("Твои категории (нажми 🗑 чтобы удалить):", reply_markup=categories_manage_kb(cats))


@router.callback_query(F.data == "delcat:new")
async def new_category_start(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup()
    await state.set_state(AddCategory.name)
    await callback.message.answer("Введи название категории (можно с эмодзи, напр: 💪 Спорт):")


@router.message(AddCategory.name)
async def new_category_name(message: Message, state: FSMContext) -> None:
    text = message.text.strip()
    parts = text.split(maxsplit=1)
    if len(parts) == 2 and len(parts[0]) <= 2:
        emoji, name = parts[0], parts[1]
    else:
        emoji, name = "📌", text

    await queries.create_category(message.from_user.id, name, emoji)
    await state.clear()
    await message.answer(f"✅ Категория «{emoji} {name}» создана!")


@router.callback_query(F.data.startswith("delcat:") & ~F.data.endswith(":new"))
async def delete_category(callback: CallbackQuery) -> None:
    cat_id = callback.data.split(":", 1)[1]
    if cat_id == "new":
        return
    await queries.delete_category(cat_id, callback.from_user.id)
    cats = await queries.get_categories(callback.from_user.id)
    await callback.message.edit_text(
        "Категория удалена. Твои категории:" if cats else "Категория удалена. Список пуст.",
        reply_markup=categories_manage_kb(cats),
    )
    await callback.answer("Удалено")
