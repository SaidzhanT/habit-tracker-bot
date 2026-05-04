from aiogram.fsm.state import State, StatesGroup


class AddHabit(StatesGroup):
    name = State()
    habit_type = State()
    counter_target = State()
    counter_unit = State()
    category = State()


class AddCategory(StatesGroup):
    name = State()
    emoji = State()


class SetReminder(StatesGroup):
    time = State()


class CounterInput(StatesGroup):
    value = State()
