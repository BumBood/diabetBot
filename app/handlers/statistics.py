from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import date, timedelta
from app.keyboards import get_statistics_keyboard, get_main_menu_keyboard
from app.utils import format_date, get_meal_type_name
from db.repository import FCIRepository, MealRecordRepository
from db.session import async_session
from db.models import MealType

router = Router()


@router.message(F.text == "📈 Статистика")
async def show_statistics_menu(message: Message):
    """Показать меню статистики"""
    text = """
📈 <b>Статистика и история</b>

Выберите период для просмотра данных:
    """

    await message.answer(text, reply_markup=get_statistics_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "stats_today")
async def show_today_stats(callback: CallbackQuery):
    """Показать статистику за сегодня"""
    today = date.today()
    await show_stats_for_date(callback, today)


@router.callback_query(F.data == "stats_yesterday")
async def show_yesterday_stats(callback: CallbackQuery):
    """Показать статистику за вчера"""
    yesterday = date.today() - timedelta(days=1)
    await show_stats_for_date(callback, yesterday)


@router.callback_query(F.data == "stats_week")
async def show_week_stats(callback: CallbackQuery):
    """Показать статистику за неделю"""
    end_date = date.today()
    start_date = end_date - timedelta(days=6)
    await show_stats_for_period(callback, start_date, end_date)


@router.callback_query(F.data == "stats_month")
async def show_month_stats(callback: CallbackQuery):
    """Показать статистику за месяц"""
    end_date = date.today()
    start_date = end_date - timedelta(days=29)
    await show_stats_for_period(callback, start_date, end_date)


async def show_stats_for_date(callback: CallbackQuery, target_date: date):
    """Показать статистику за конкретную дату"""
    async with async_session() as session:
        fci_repo = FCIRepository(session)
        meal_repo = MealRecordRepository(session)

        # Получаем ФЧИ за эту дату
        fci_record = await fci_repo.get_by_date(target_date)

        # Получаем записи о приёмах пищи за эту дату
        meal_records = await meal_repo.get_by_date(target_date)

        # Группируем по типам приёмов пищи
        meals_by_type = {}
        for record in meal_records:
            meals_by_type[record.meal_type] = record

        text = f"📊 <b>Статистика за {format_date(target_date)}</b>\n\n"

        if fci_record:
            text += f"📈 <b>ФЧИ:</b> {fci_record.value:.2f}\n\n"
        else:
            text += "📈 <b>ФЧИ:</b> Не рассчитан\n\n"

        text += "🍽️ <b>УК по приёмам пищи:</b>\n"

        for meal_type in [MealType.BREAKFAST, MealType.LUNCH, MealType.SNACK, MealType.DINNER]:
            meal_name = get_meal_type_name(meal_type)
            if meal_type in meals_by_type:
                record = meals_by_type[meal_type]
                text += f"• {meal_name}: {record.uk_value:.3f}\n"
            else:
                text += f"• {meal_name}: Не рассчитан\n"

        if not meal_records:
            text += "\n❌ За эту дату нет записей о приёмах пищи"

        await callback.message.edit_text(text, parse_mode="HTML")
        await callback.answer()


async def show_stats_for_period(callback: CallbackQuery, start_date: date, end_date: date):
    """Показать статистику за период"""
    async with async_session() as session:
        fci_repo = FCIRepository(session)
        meal_repo = MealRecordRepository(session)

        # Получаем ФЧИ за период
        fci_records = await fci_repo.get_by_date_range(start_date, end_date)

        # Получаем записи о приёмах пищи за период
        meal_records = await meal_repo.get_by_date_range(start_date, end_date)

        text = f"📊 <b>Статистика за период {format_date(start_date)} - {format_date(end_date)}</b>\n\n"

        # Статистика ФЧИ
        if fci_records:
            fci_values = [record.value for record in fci_records]
            avg_fci = sum(fci_values) / len(fci_values)
            text += f"📈 <b>ФЧИ:</b>\n"
            text += f"• Количество записей: {len(fci_records)}\n"
            text += f"• Среднее значение: {avg_fci:.2f}\n"
            text += f"• Минимум: {min(fci_values):.2f}\n"
            text += f"• Максимум: {max(fci_values):.2f}\n\n"
        else:
            text += "📈 <b>ФЧИ:</b> Нет данных\n\n"

        # Статистика УК по типам приёмов пищи
        text += "🍽️ <b>УК по приёмам пищи:</b>\n"

        for meal_type in [MealType.BREAKFAST, MealType.LUNCH, MealType.SNACK, MealType.DINNER]:
            meal_name = get_meal_type_name(meal_type)
            type_records = [r for r in meal_records if r.meal_type == meal_type]

            if type_records:
                uk_values = [record.uk_value for record in type_records]
                avg_uk = sum(uk_values) / len(uk_values)
                text += f"• {meal_name}: {len(type_records)} записей, среднее УК: {avg_uk:.3f}\n"
            else:
                text += f"• {meal_name}: Нет данных\n"

        if not meal_records:
            text += "\n❌ За этот период нет записей о приёмах пищи"

        await callback.message.edit_text(text, parse_mode="HTML")
        await callback.answer()


@router.message(F.text == "❓ Помощь")
async def show_help(message: Message):
    """Показать справку"""
    help_text = """
❓ <b>Справка по DiabetBot</b>

<b>Основные функции:</b>

📊 <b>Рассчитать ФЧИ</b>
• Собирает данные об ультракоротком инсулине за 3 дня
• Рассчитывает формулу чувствительности к инсулину
• Сохраняет результат для использования в расчётах УК

🍽️ <b>Рассчитать УК</b>
• Пошаговый ввод данных о приёме пищи
• Учитывает подколки с автоматической коррекцией
• Рассчитывает условный коэффициент для планирования

📈 <b>Статистика</b>
• Просмотр истории ФЧИ и УК
• Статистика за разные периоды
• Средние значения и тренды

<b>Формулы:</b>

• <b>ФЧИ</b> = 100 / Среднее_значение_инсулина_за_3_дня
• <b>УК</b> = ((СК_отработка - СК_старт) / ФЧИ + Инсулин_еда + Инсулин_подколки) / Углеводы

<b>Коррекция подколок:</b>
• 1 час после еды → × 0.85
• 2 часа после еды → × 0.6  
• 3 часа после еды → × 0.25

<b>Поддержка:</b>
Если у вас есть вопросы или проблемы, обратитесь к разработчику.
    """

    await message.answer(help_text, parse_mode="HTML")
