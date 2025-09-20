from datetime import date, datetime, timedelta
from typing import Tuple
from db.models import MealType


def get_date_suggestions() -> Tuple[date, date, date]:
    """Возвращает даты для ввода ФЧИ (позавчера, вчера, сегодня)"""
    today = date.today()
    yesterday = today - timedelta(days=1)
    day_before_yesterday = today - timedelta(days=2)
    return day_before_yesterday, yesterday, today


def format_date(date_obj: date) -> str:
    """Форматирует дату для отображения"""
    return date_obj.strftime("%d.%m.%Y")


def calculate_fci(day1: float, day2: float, day3: float) -> float:
    """Рассчитывает ФЧИ по формуле"""
    average = (day1 + day2 + day3) / 3
    return 100 / average


def calculate_injection_correction(time_from_meal_minutes: int) -> float:
    """Рассчитывает коэффициент коррекции для подколок"""
    if time_from_meal_minutes <= 60:
        return 0.85
    elif time_from_meal_minutes <= 120:
        return 0.6
    elif time_from_meal_minutes <= 180:
        return 0.25
    else:
        return 0.0


def calculate_uk(
    glucose_start: float,
    glucose_end: float,
    fci: float,
    insulin_food: float,
    insulin_additional: float,
    carbs_main: float,
    carbs_additional: float,
) -> float:
    """Рассчитывает УК по формуле"""
    if carbs_main + carbs_additional == 0:
        return 0.0

    numerator = (glucose_end - glucose_start) / fci + insulin_food + insulin_additional
    denominator = carbs_main + carbs_additional

    return numerator / denominator


def get_meal_type_name(meal_type: MealType) -> str:
    """Возвращает русское название типа приёма пищи"""
    names = {MealType.BREAKFAST: "Завтрак", MealType.LUNCH: "Обед", MealType.SNACK: "Полдник", MealType.DINNER: "Ужин"}
    return names.get(meal_type, meal_type.value)


def parse_glucose_input(text: str) -> float:
    """Парсит ввод уровня глюкозы"""
    try:
        # Убираем все кроме цифр, точек и запятых
        cleaned = "".join(c for c in text if c.isdigit() or c in ".,")
        # Заменяем запятую на точку
        cleaned = cleaned.replace(",", ".")
        return float(cleaned)
    except (ValueError, TypeError):
        raise ValueError("Неверный формат уровня глюкозы")


def parse_number_input(text: str) -> float:
    """Парсит числовой ввод"""
    try:
        cleaned = "".join(c for c in text if c.isdigit() or c in ".,")
        cleaned = cleaned.replace(",", ".")
        return float(cleaned)
    except (ValueError, TypeError):
        raise ValueError("Неверный формат числа")
