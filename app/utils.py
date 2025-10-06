from datetime import date, timedelta
from typing import Tuple
from db.models import MealType


def get_date_suggestions() -> Tuple[date, date, date]:
    """Возвращает даты для ввода ФЧИ (вчера, позавчера, позапозавчера)"""
    today = date.today()
    yesterday = today - timedelta(days=1)
    day_before_yesterday = today - timedelta(days=2)
    day_before_before_yesterday = today - timedelta(days=3)
    return yesterday, day_before_yesterday, day_before_before_yesterday


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
    proteins: float | None = None,
    fats: float | None = None,
) -> float:
    """Рассчитывает УК по формуле с учётом БЖУ.

    Спекулятивно: учитываем энергетический вклад белков и жиров в пересчёте на условные "углеводные граммы".
    Простой приближенный перевод (можно скорректировать под твою методику):
      - белки: 4 ккал/г → эквивалент углеводов по влиянию: 0.1 г углеводов на 1 г белка (фактор 0.1)
      - жиры: 9 ккал/г → медленное влияние: 0.05 г углеводов на 1 г жира (фактор 0.05)
    Если нужны другие коэффициенты — скажи, вынесу их в настройки.
    """
    if carbs_main + carbs_additional == 0 and not proteins and not fats:
        return 0.0

    proteins = proteins or 0.0
    fats = fats or 0.0

    # Условная карб-эквивалентность Б/Ж
    protein_carb_eq = 0.1 * proteins
    fat_carb_eq = 0.05 * fats

    effective_carbs = carbs_main + carbs_additional + protein_carb_eq + fat_carb_eq
    if effective_carbs <= 0:
        return 0.0

    numerator = (glucose_end - glucose_start) / fci + insulin_food + insulin_additional
    uk = (numerator / effective_carbs) * 10
    return uk


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


async def calculate_daily_insulin_from_meals(user_id: int, target_date: date, session) -> float:
    """Рассчитывает общий инсулин за день из записей о приёмах пищи"""
    from db.repository import MealRecordRepository

    meal_repo = MealRecordRepository(session)
    meals = await meal_repo.get_by_date(user_id, target_date)

    total_insulin = 0.0
    for meal in meals:
        # Инсулин на еду + дополнительный инсулин (подколки)
        total_insulin += float(meal.insulin_food) + float(meal.insulin_additional)

    return total_insulin


async def get_insulin_for_fci(user_id: int, target_date: date, session) -> float:
    """
    Получает ВЕСЬ инсулин за день для расчета ФЧИ.

    Приоритет:
    1. Ручной ввод (is_manual=1) - если пользователь вручную ввел инсулин для этого дня
    2. Автоматические записи (is_manual=0) - суммирование всех записей из приемов пищи
    3. Суммирование из meal_records - если нет записей в insulin_records
    """
    from db.repository import MealRecordRepository, InsulinRecordRepository

    insulin_repo = InsulinRecordRepository(session)

    # Приоритет 1: Ручной ввод (пользователь вручную ввел данные для ФЧИ)
    manual_total = await insulin_repo.get_manual_total_by_date(user_id, target_date)
    if manual_total > 0:
        return manual_total

    # Приоритет 2: Автоматические записи (суммируются все записи из приемов пищи)
    auto_total = await insulin_repo.get_auto_total_by_date(user_id, target_date)
    if auto_total > 0:
        return auto_total

    # Приоритет 3: Суммирование напрямую из meal_records (если нет записей в insulin_records)
    meal_repo = MealRecordRepository(session)
    meals = await meal_repo.get_by_date(user_id, target_date)

    meal_insulin = 0.0
    if meals:
        for meal in meals:
            meal_insulin += float(meal.insulin_food) + float(meal.insulin_additional)

    return meal_insulin
