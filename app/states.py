from aiogram.fsm.state import State, StatesGroup


class FCIStates(StatesGroup):
    waiting_for_day1 = State()
    waiting_for_day2 = State()
    waiting_for_day3 = State()


class MealStates(StatesGroup):
    waiting_for_meal_type = State()
    waiting_for_glucose_start = State()
    waiting_for_pause_time = State()
    waiting_for_carbs_main = State()
    waiting_for_carbs_additional = State()
    waiting_for_proteins = State()
    waiting_for_insulin_food = State()
    waiting_for_glucose_end = State()
    waiting_for_additional_injections = State()
    waiting_for_additional_carbs = State()


class StatisticsStates(StatesGroup):
    waiting_for_date_range = State()
