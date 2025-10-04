from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from app.states import FCIStates
from app.keyboards import get_main_menu_keyboard, get_cancel_keyboard
from app.utils import get_date_suggestions, format_date, calculate_fci, parse_number_input
from db.repository import FCIRepository, InsulinRecordRepository
from db.models import InsulinType
from db.session import async_session

router = Router()


@router.message(F.text == "📊 Рассчитать ФЧИ")
async def start_fci_calculation(message: Message, state: FSMContext, user):
    """Начало расчёта ФЧИ"""
    day1, day2, day3 = get_date_suggestions()

    async with async_session() as session:
        insulin_repo = InsulinRecordRepository(session)

        # Получаем данные за предыдущие дни из БД
        day1_total = await insulin_repo.get_total_by_date(user.id, day1)
        day2_total = await insulin_repo.get_total_by_date(user.id, day2)

        # Если есть данные за оба предыдущих дня, сразу переходим к третьему дню
        if day1_total > 0 and day2_total > 0:
            text = f"""
📊 <b>Расчёт ФЧИ (формула чувствительности к инсулину)</b>

Найдены данные за предыдущие дни:
• <b>{format_date(day1)}</b>: {day1_total:.1f} ед.
• <b>{format_date(day2)}</b>: {day2_total:.1f} ед.

Введите количество ультракороткого инсулина за <b>{format_date(day3)}</b>:
            """

            await state.set_state(FCIStates.waiting_for_day3)
            await state.update_data(
                day1_date=day1, day2_date=day2, day3_date=day3, day1_value=day1_total, day2_value=day2_total
            )
            await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
            return

        # Если нет данных за первый день, начинаем с него
        elif day1_total == 0:
            text = f"""
📊 <b>Расчёт ФЧИ (формула чувствительности к инсулину)</b>

Мне нужно собрать данные о количестве ультракороткого инсулина на еду и коррекции (сколы) с 8:00 до 24:00 за три дня:

• <b>Вчера</b> ({format_date(day1)})
• <b>Позавчера</b> ({format_date(day2)})
• <b>Позапозавчера</b> ({format_date(day3)})

⚠️ <b>Важно:</b> В расчёт НЕ включается базальный (фоновой) инсулин!

Начнём с вчерашнего дня. Введите общее количество ультракороткого инсулина за {format_date(day1)}:
            """

            await state.set_state(FCIStates.waiting_for_day1)
            await state.update_data(day1_date=day1, day2_date=day2, day3_date=day3)
            await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")

        # Если есть данные только за первый день, начинаем со второго
        else:
            text = f"""
📊 <b>Расчёт ФЧИ (формула чувствительности к инсулину)</b>

Найденные данные из БД:
• <b>{format_date(day1)}</b>: {day1_total:.1f} ед. ✅

Введите количество ультракороткого инсулина за <b>{format_date(day2)}</b>:
            """

            await state.set_state(FCIStates.waiting_for_day2)
            await state.update_data(day1_date=day1, day2_date=day2, day3_date=day3, day1_value=day1_total)
            await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")


@router.message(FCIStates.waiting_for_day1)
async def process_day1_input(message: Message, state: FSMContext, user):
    """Обработка ввода данных за день 1"""
    try:
        day1_value = parse_number_input(message.text or "")
        if day1_value <= 0:
            await message.answer(
                "❌ Количество инсулина должно быть больше 0. Попробуйте ещё раз:", reply_markup=get_cancel_keyboard()
            )
            return

        data = await state.get_data()

        # Сохраняем данные инсулина в БД
        async with async_session() as session:
            insulin_repo = InsulinRecordRepository(session)
            await insulin_repo.create(
                user_id=user.id,
                date=data["day1_date"],
                insulin_type=InsulinType.FOOD,  # Пока что сохраняем как "на еду", можно будет разбить на типы позже
                amount=day1_value,
            )

        await state.update_data(day1_value=day1_value)

        text = f"""
✅ Данные за {format_date(data["day1_date"])}: {day1_value} ед. (сохранено в БД)

Теперь введите количество ультракороткого инсулина за {format_date(data["day2_date"])}:
        """

        await state.set_state(FCIStates.waiting_for_day2)
        await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")

    except ValueError:
        await message.answer(
            "❌ Неверный формат числа. Введите количество инсулина числом (например: 25.5):",
            reply_markup=get_cancel_keyboard(),
        )


@router.message(FCIStates.waiting_for_day2)
async def process_day2_input(message: Message, state: FSMContext, user):
    """Обработка ввода данных за день 2"""
    try:
        day2_value = parse_number_input(message.text or "")
        if day2_value <= 0:
            await message.answer(
                "❌ Количество инсулина должно быть больше 0. Попробуйте ещё раз:", reply_markup=get_cancel_keyboard()
            )
            return

        data = await state.get_data()

        # Сохраняем данные инсулина в БД
        async with async_session() as session:
            insulin_repo = InsulinRecordRepository(session)
            await insulin_repo.create(
                user_id=user.id,
                date=data["day2_date"],
                insulin_type=InsulinType.FOOD,  # Пока что сохраняем как "на еду", можно будет разбить на типы позже
                amount=day2_value,
            )

        await state.update_data(day2_value=day2_value)

        text = f"""
✅ Данные за {format_date(data["day2_date"])}: {day2_value} ед. (сохранено в БД)

Теперь введите количество ультракороткого инсулина за {format_date(data["day3_date"])}:
        """

        await state.set_state(FCIStates.waiting_for_day3)
        await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")

    except ValueError:
        await message.answer(
            "❌ Неверный формат числа. Введите количество инсулина числом (например: 25.5):",
            reply_markup=get_cancel_keyboard(),
        )


@router.message(FCIStates.waiting_for_day3)
async def process_day3_input(message: Message, state: FSMContext, user):
    """Обработка ввода данных за день 3 и расчёт ФЧИ"""
    try:
        day3_value = parse_number_input(message.text or "")
        if day3_value <= 0:
            await message.answer(
                "❌ Количество инсулина должно быть больше 0. Попробуйте ещё раз:", reply_markup=get_cancel_keyboard()
            )
            return

        data = await state.get_data()
        day1_value = data["day1_value"]
        day2_value = data["day2_value"]

        # Сохраняем данные третьего дня в БД
        async with async_session() as session:
            insulin_repo = InsulinRecordRepository(session)
            fci_repo = FCIRepository(session)

            # Сохраняем инсулин за третий день
            await insulin_repo.create(
                user_id=user.id,
                date=data["day3_date"],
                insulin_type=InsulinType.FOOD,  # Пока что сохраняем как "на еду", можно будет разбить на типы позже
                amount=day3_value,
            )

            # Рассчитываем и сохраняем ФЧИ
            fci_value = calculate_fci(day1_value, day2_value, day3_value)
            await fci_repo.create(user_id=user.id, date=data["day3_date"], value=fci_value)

        result_text = f"""
🎉 <b>Расчёт ФЧИ завершён!</b>

📊 <b>Данные:</b>
• {format_date(data["day1_date"])}: {day1_value} ед.
• {format_date(data["day2_date"])}: {day2_value} ед.  
• {format_date(data["day3_date"])}: {day3_value} ед.

📈 <b>Результат:</b>
• Среднее значение: {(day1_value + day2_value + day3_value) / 3:.2f} ед.
• <b>ФЧИ = {fci_value:.2f}</b>

✅ Данные сохранены! Теперь вы можете использовать этот ФЧИ для расчёта УК.
        """

        await state.clear()
        await message.answer(result_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())

    except ValueError:
        await message.answer(
            "❌ Неверный формат числа. Введите количество инсулина числом (например: 25.5):",
            reply_markup=get_cancel_keyboard(),
        )
