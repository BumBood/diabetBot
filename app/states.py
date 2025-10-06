from aiogram.fsm.state import State, StatesGroup


class FCIStates(StatesGroup):
    waiting_for_day1 = State()
    waiting_for_day2 = State()
    waiting_for_day3 = State()
    waiting_for_correction_date = State()
    waiting_for_correction_amount = State()
    waiting_for_edit_date = State()
    waiting_for_edit_value = State()


class MealStates(StatesGroup):
    waiting_for_meal_type = State()
    waiting_for_glucose_start = State()
    waiting_for_pause_time = State()
    waiting_for_carbs_main = State()
    waiting_for_carbs_additional = State()
    waiting_for_proteins = State()
    waiting_for_fats = State()
    waiting_for_insulin_food = State()
    waiting_for_glucose_end = State()
    waiting_for_additional_injections = State()
    waiting_for_additional_carbs = State()


class StatisticsStates(StatesGroup):
    waiting_for_date_range = State()


class CaloriesStates(StatesGroup):
    waiting_for_gender = State()
    waiting_for_age_years = State()
    waiting_for_weight_kg = State()
    waiting_for_height_cm = State()
    waiting_for_activity = State()
    waiting_for_metabolic_range = State()
