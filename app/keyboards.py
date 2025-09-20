from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from db.models import MealType


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню бота"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
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
