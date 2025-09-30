from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from db.models import MealType


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🔥 Расчет калорий")],
            [KeyboardButton(text="📊 Рассчитать ФЧИ")],
            [KeyboardButton(text="🍽️ Рассчитать УК")],
            [KeyboardButton(text="📈 Статистика")],
            [KeyboardButton(text="❓ Помощь")],
        ],
        resize_keyboard=True,
        one_time_keyboard=False,
    )
    return keyboard


def get_meal_type_keyboard() -> InlineKeyboardMarkup:
    """Выбор типа приёма пищи"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌅 Завтрак", callback_data="meal_breakfast")],
            [InlineKeyboardButton(text="🌞 Обед", callback_data="meal_lunch")],
            [InlineKeyboardButton(text="☕ Полдник", callback_data="meal_snack")],
            [InlineKeyboardButton(text="🌙 Ужин", callback_data="meal_dinner")],
        ]
    )
    return keyboard


def get_yes_no_keyboard() -> InlineKeyboardMarkup:
    """Да/Нет клавиатура"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Да", callback_data="yes")],
            [InlineKeyboardButton(text="❌ Нет", callback_data="no")],
        ]
    )
    return keyboard


def get_additional_injection_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для дополнительных подколок"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить подколку", callback_data="add_injection")],
            [InlineKeyboardButton(text="✅ Завершить", callback_data="finish_injections")],
        ]
    )
    return keyboard


def get_additional_carbs_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для дополнительных углеводов"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить углеводы", callback_data="add_carbs")],
            [InlineKeyboardButton(text="✅ Пропустить", callback_data="skip_carbs")],
        ]
    )
    return keyboard


def get_time_from_meal_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора времени подколки"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="1 час", callback_data="time_60")],
            [InlineKeyboardButton(text="2 часа", callback_data="time_120")],
            [InlineKeyboardButton(text="3 часа", callback_data="time_180")],
        ]
    )
    return keyboard


def get_skip_proteins_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура: добавить белки или пропустить"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Ввести белки", callback_data="enter_proteins")],
            [InlineKeyboardButton(text="✅ Пропустить белки", callback_data="skip_proteins")],
        ]
    )
    return keyboard


def get_statistics_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для статистики"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 За сегодня", callback_data="stats_today")],
            [InlineKeyboardButton(text="📆 За вчера", callback_data="stats_yesterday")],
            [InlineKeyboardButton(text="📊 За неделю", callback_data="stats_week")],
            [InlineKeyboardButton(text="📈 За месяц", callback_data="stats_month")],
        ]
    )
    return keyboard


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для отмены ввода"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="❌ Отменить ввод", callback_data="cancel_input")]]
    )
    return keyboard


def get_calories_gender_keyboard() -> InlineKeyboardMarkup:
    """Выбор пола для расчёта калорий"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="👦 Мальчик", callback_data="cal_gender_male")],
            [InlineKeyboardButton(text="👧 Девочка", callback_data="cal_gender_female")],
        ]
    )
    return keyboard


def get_calories_activity_keyboard(gender: str) -> InlineKeyboardMarkup:
    """Выбор коэффициента активности в зависимости от пола"""
    if gender == "male":
        rows = [
            [InlineKeyboardButton(text="Сидячий образ жизни", callback_data="cal_act_male_sedentary")],
            [InlineKeyboardButton(text="Низкая активность", callback_data="cal_act_male_low")],
            [InlineKeyboardButton(text="Средняя активность", callback_data="cal_act_male_medium")],
            [InlineKeyboardButton(text="Большая активность", callback_data="cal_act_male_high")],
        ]
    else:
        rows = [
            [InlineKeyboardButton(text="Сидячий образ жизни", callback_data="cal_act_female_sedentary")],
            [InlineKeyboardButton(text="Низкая активность", callback_data="cal_act_female_low")],
            [InlineKeyboardButton(text="Средняя активность", callback_data="cal_act_female_medium")],
            [InlineKeyboardButton(text="Большая активность", callback_data="cal_act_female_high")],
        ]

    keyboard = InlineKeyboardMarkup(inline_keyboard=rows)
    return keyboard
