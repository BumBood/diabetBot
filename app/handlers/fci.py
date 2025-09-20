from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import date, timedelta
from app.states import FCIStates
from app.keyboards import get_main_menu_keyboard, get_yes_no_keyboard
from app.utils import get_date_suggestions, format_date, calculate_fci, parse_number_input
from db.repository import FCIRepository
from db.session import async_session

router = Router()


class FCIStates(StatesGroup):
    waiting_for_day1 = State()
    waiting_for_day2 = State()
    waiting_for_day3 = State()


@router.message(F.text == "📊 Рассчитать ФЧИ")
async def start_fci_calculation(message: Message, state: FSMContext):
    """Начало расчёта ФЧИ"""
    day1, day2, day3 = get_date_suggestions()

    explanation_text = f"""
📊 <b>Расчёт ФЧИ (формула чувствительности к инсулину)</b>

Мне нужно собрать данные о количестве ультракороткого инсулина на еду и коррекции (сколы) с 8:00 до 24:00 за три дня:

• <b>Позавчера</b> ({format_date(day1)})
• <b>Вчера</b> ({format_date(day2)})  
• <b>Сегодня</b> ({format_date(day3)})

⚠️ <b>Важно:</b> В расчёт НЕ включается базальный (фоновой) инсулин!

Начнём с позавчерашнего дня. Введите общее количество ультракороткого инсулина за {format_date(day1)}:
    """

    await state.set_state(FCIStates.waiting_for_day1)
    await state.update_data(day1_date=day1, day2_date=day2, day3_date=day3)
    await message.answer(explanation_text, parse_mode="HTML")


@router.message(FCIStates.waiting_for_day1)
async def process_day1_input(message: Message, state: FSMContext):
    """Обработка ввода данных за день 1"""
    try:
        day1_value = parse_number_input(message.text)
        if day1_value <= 0:
            await message.answer("❌ Количество инсулина должно быть больше 0. Попробуйте ещё раз:")
            return

        await state.update_data(day1_value=day1_value)
        data = await state.get_data()

        text = f"""
✅ Данные за {format_date(data["day1_date"])}: {day1_value} ед.

Теперь введите количество ультракороткого инсулина за {format_date(data["day2_date"])}:
        """

        await state.set_state(FCIStates.waiting_for_day2)
        await message.answer(text, parse_mode="HTML")

    except ValueError:
        await message.answer("❌ Неверный формат числа. Введите количество инсулина числом (например: 25.5):")


@router.message(FCIStates.waiting_for_day2)
async def process_day2_input(message: Message, state: FSMContext):
    """Обработка ввода данных за день 2"""
    try:
        day2_value = parse_number_input(message.text)
        if day2_value <= 0:
            await message.answer("❌ Количество инсулина должно быть больше 0. Попробуйте ещё раз:")
            return

        await state.update_data(day2_value=day2_value)
        data = await state.get_data()

        text = f"""
✅ Данные за {format_date(data["day2_date"])}: {day2_value} ед.

Теперь введите количество ультракороткого инсулина за {format_date(data["day3_date"])}:
        """

        await state.set_state(FCIStates.waiting_for_day3)
        await message.answer(text, parse_mode="HTML")

    except ValueError:
        await message.answer("❌ Неверный формат числа. Введите количество инсулина числом (например: 25.5):")


@router.message(FCIStates.waiting_for_day3)
async def process_day3_input(message: Message, state: FSMContext):
    """Обработка ввода данных за день 3 и расчёт ФЧИ"""
    try:
        day3_value = parse_number_input(message.text)
        if day3_value <= 0:
            await message.answer("❌ Количество инсулина должно быть больше 0. Попробуйте ещё раз:")
            return

        data = await state.get_data()
        day1_value = data["day1_value"]
        day2_value = data["day2_value"]

        # Рассчитываем ФЧИ
        fci_value = calculate_fci(day1_value, day2_value, day3_value)

        # Сохраняем в базу данных
        async with async_session() as session:
            fci_repo = FCIRepository(session)
            await fci_repo.create(date=data["day3_date"], value=fci_value)

        result_text = f"""
🎉 <b>Расчёт ФЧИ завершён!</b>

📊 <b>Данные:</b>
• {format_date(data["day1_date"])}: {day1_value} ед.
• {format_date(data["day2_date"])}: {day2_value} ед.  
• {format_date(data["day3_date"])}: {day3_value} ед.

📈 <b>Результат:</b>
• Среднее значение: {(day1_value + day2_value + day3_value) / 3:.2f} ед.
• <b>ФЧИ = {fci_value:.2f}</b>

Данные сохранены! Теперь вы можете использовать этот ФЧИ для расчёта УК.
        """

        await state.clear()
        await message.answer(result_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())

    except ValueError:
        await message.answer("❌ Неверный формат числа. Введите количество инсулина числом (например: 25.5):")
