from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from app.states import FCIStates
from app.keyboards import (
    get_main_menu_keyboard,
    get_cancel_keyboard,
    get_fci_correction_keyboard,
    get_fci_edit_keyboard,
)
from app.utils import (
    get_date_suggestions,
    format_date,
    calculate_fci,
    parse_number_input,
    get_insulin_for_fci,
)
from db.repository import FCIRepository, InsulinRecordRepository
from db.models import InsulinType
from db.session import async_session

router = Router()


@router.message(F.text == "📊 Рассчитать ФЧИ")
async def start_fci_calculation(message: Message, state: FSMContext, user):
    """Начало расчёта ФЧИ"""
    day1, day2, day3 = get_date_suggestions()

    async with async_session() as session:
        # Получаем данные с приоритетом: meal_records > manual insulin > auto insulin
        day1_total = await get_insulin_for_fci(user.id, day1, session)
        day2_total = await get_insulin_for_fci(user.id, day2, session)
        day3_total = await get_insulin_for_fci(user.id, day3, session)

        # Если есть данные за все три дня, сразу переходим к расчёту
        if day1_total > 0 and day2_total > 0 and day3_total > 0:
            fci_value = calculate_fci(day1_total, day2_total, day3_total)

            fci_repo = FCIRepository(session)
            await fci_repo.update_or_create(user_id=user.id, date=day1, value=fci_value)

            result_text = f"""
🎉 <b>Расчёт ФЧИ завершён!</b>

📊 <b>Данные:</b>
• {format_date(day1)}: {day1_total:.1f} ед.
• {format_date(day2)}: {day2_total:.1f} ед.  
• {format_date(day3)}: {day3_total:.1f} ед.

📈 <b>Результат:</b>
• Среднее значение: {(day1_total + day2_total + day3_total) / 3:.2f} ед.
• <b>ФЧИ = {fci_value:.2f}</b>

✅ Данные сохранены! Теперь вы можете использовать этот ФЧИ для расчёта УК.
            """

            await state.clear()
            await message.answer(result_text, parse_mode="HTML", reply_markup=get_fci_edit_keyboard())
            await message.answer("Выберите действие:", reply_markup=get_main_menu_keyboard())
            return

        # Определяем, какие дни нужно запросить
        missing_days = []
        if day1_total == 0:
            missing_days.append((1, day1))
        if day2_total == 0:
            missing_days.append((2, day2))
        if day3_total == 0:
            missing_days.append((3, day3))

        # Если нет данных за вчера (day1), начинаем с него
        if day1_total == 0:
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

        # Если есть данные за вчера, но нет за позавчера, спрашиваем позавчера
        elif day2_total == 0:
            text = f"""
📊 <b>Расчёт ФЧИ (формула чувствительности к инсулину)</b>

Найденные данные из БД:
• <b>{format_date(day1)}</b>: {day1_total:.1f} ед. ✅

Введите количество ультракороткого инсулина за <b>{format_date(day2)}</b>:
            """

            text += "\n\n💡 <i>Данные за вчера взяты из БД. Если нужно исправить — используйте кнопку ниже.</i>"
            await message.answer(text, reply_markup=get_fci_correction_keyboard(), parse_mode="HTML")

            await state.set_state(FCIStates.waiting_for_day2)
            await state.update_data(day1_date=day1, day2_date=day2, day3_date=day3, day1_value=day1_total)

        # Если есть данные за вчера и позавчера, но нет за позапозавчера, спрашиваем позапозавчера
        elif day3_total == 0:
            text = f"""
📊 <b>Расчёт ФЧИ (формула чувствительности к инсулину)</b>

Найдены данные за предыдущие дни:
• <b>{format_date(day1)}</b>: {day1_total:.1f} ед.
• <b>{format_date(day2)}</b>: {day2_total:.1f} ед.

Введите количество ультракороткого инсулина за <b>{format_date(day3)}</b>:
            """

            text += "\n\n💡 <i>Данные взяты из БД. Если нужно исправить — используйте кнопку ниже.</i>"
            await message.answer(text, reply_markup=get_fci_correction_keyboard(), parse_mode="HTML")

            await state.set_state(FCIStates.waiting_for_day3)
            await state.update_data(
                day1_date=day1, day2_date=day2, day3_date=day3, day1_value=day1_total, day2_value=day2_total
            )


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

        # Сохраняем данные инсулина в БД как ручной ввод
        async with async_session() as session:
            insulin_repo = InsulinRecordRepository(session)
            await insulin_repo.create(
                user_id=user.id,
                date=data["day1_date"],
                insulin_type=InsulinType.FOOD,
                amount=day1_value,
                is_manual=True,  # Первый ввод при начале пользования ботом
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

        # Сохраняем данные инсулина в БД как ручной ввод
        async with async_session() as session:
            insulin_repo = InsulinRecordRepository(session)
            await insulin_repo.create(
                user_id=user.id,
                date=data["day2_date"],
                insulin_type=InsulinType.FOOD,
                amount=day2_value,
                is_manual=True,  # Первый ввод при начале пользования ботом
            )

        await state.update_data(day2_value=day2_value)

        # Проверяем, есть ли данные для day3
        async with async_session() as session:
            day3_total = await get_insulin_for_fci(user.id, data["day3_date"], session)

        if day3_total > 0:
            # Есть данные за day3, можно сразу рассчитать ФЧИ
            day1_value = data["day1_value"]
            fci_value = calculate_fci(day1_value, day2_value, day3_total)

            async with async_session() as session:
                fci_repo = FCIRepository(session)
                await fci_repo.update_or_create(user_id=user.id, date=data["day1_date"], value=fci_value)

            result_text = f"""
🎉 <b>Расчёт ФЧИ завершён!</b>

📊 <b>Данные:</b>
• {format_date(data["day1_date"])}: {day1_value} ед.
• {format_date(data["day2_date"])}: {day2_value} ед.  
• {format_date(data["day3_date"])}: {day3_total:.1f} ед.

📈 <b>Результат:</b>
• Среднее значение: {(day1_value + day2_value + day3_total) / 3:.2f} ед.
• <b>ФЧИ = {fci_value:.2f}</b>

✅ Данные сохранены! Теперь вы можете использовать этот ФЧИ для расчёта УК.
            """

            await state.clear()
            await message.answer(result_text, parse_mode="HTML", reply_markup=get_fci_edit_keyboard())
            await message.answer("Выберите действие:", reply_markup=get_main_menu_keyboard())
            return

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

            # Сохраняем инсулин за третий день как ручной ввод
            await insulin_repo.create(
                user_id=user.id,
                date=data["day3_date"],
                insulin_type=InsulinType.FOOD,
                amount=day3_value,
                is_manual=True,  # Первый ввод при начале пользования ботом
            )

            # Рассчитываем и сохраняем ФЧИ
            fci_value = calculate_fci(day1_value, day2_value, day3_value)
            await fci_repo.update_or_create(user_id=user.id, date=data["day3_date"], value=fci_value)

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
        await message.answer(result_text, parse_mode="HTML", reply_markup=get_fci_edit_keyboard())
        await message.answer("Выберите действие:", reply_markup=get_main_menu_keyboard())

    except ValueError:
        await message.answer(
            "❌ Неверный формат числа. Введите количество инсулина числом (например: 25.5):",
            reply_markup=get_cancel_keyboard(),
        )


@router.callback_query(F.data == "fci_correct_day")
async def start_correction(callback: CallbackQuery, state: FSMContext):
    """Начало исправления данных за день"""
    await state.set_state(FCIStates.waiting_for_correction_date)

    text = """
✏️ <b>Исправление данных за день</b>

Введите дату в формате ДД.ММ.ГГГГ (например: 15.10.2024):
    """

    if callback.message and hasattr(callback.message, "edit_text"):
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_cancel_keyboard())
    elif callback.bot:
        await callback.bot.send_message(
            chat_id=callback.from_user.id, text=text, parse_mode="HTML", reply_markup=get_cancel_keyboard()
        )
    await callback.answer()


@router.message(FCIStates.waiting_for_correction_date)
async def process_correction_date(message: Message, state: FSMContext):
    """Обработка ввода даты для исправления"""
    try:
        from datetime import datetime

        # Парсим дату
        date_str = (message.text or "").strip()
        date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()

        await state.update_data(correction_date=date_obj)
        await state.set_state(FCIStates.waiting_for_correction_amount)

        text = f"""
✅ Дата: {format_date(date_obj)}

Введите правильное количество ультракороткого инсулина за этот день:
        """

        await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")

    except ValueError:
        await message.answer(
            "❌ Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ (например: 15.10.2024):",
            reply_markup=get_cancel_keyboard(),
        )


@router.message(FCIStates.waiting_for_correction_amount)
async def process_correction_amount(message: Message, state: FSMContext, user):
    """Обработка ввода исправленного количества инсулина"""
    try:
        amount = parse_number_input(message.text or "")
        if amount < 0:
            await message.answer(
                "❌ Количество инсулина не может быть отрицательным. Попробуйте ещё раз:",
                reply_markup=get_cancel_keyboard(),
            )
            return

        data = await state.get_data()
        correction_date = data["correction_date"]

        # Сохраняем исправленные данные в insulin_records (заменяет предыдущие ручные записи)
        async with async_session() as session:
            insulin_repo = InsulinRecordRepository(session)
            await insulin_repo.update_or_create_manual(
                user_id=user.id,
                target_date=correction_date,
                insulin_type=InsulinType.FOOD,
                amount=amount,
            )

        text = f"""
✅ <b>Данные исправлены!</b>

📅 Дата: {format_date(correction_date)}
💉 Инсулин: {amount} ед.

Теперь можно продолжить расчёт ФЧИ с исправленными данными.
        """

        await state.clear()
        await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())

    except ValueError:
        await message.answer(
            "❌ Неверный формат числа. Введите количество инсулина числом (например: 25.5):",
            reply_markup=get_cancel_keyboard(),
        )


@router.callback_query(F.data == "fci_continue")
async def continue_fci_calculation(callback: CallbackQuery, state: FSMContext):
    """Продолжение расчёта ФЧИ без исправлений"""
    data = await state.get_data()

    # Определяем, на каком этапе мы остановились
    if "day1_value" in data and "day2_value" not in data:
        # Нужно ввести данные за day2
        text = f"""
✅ Продолжаем расчёт ФЧИ

Введите количество ультракороткого инсулина за {format_date(data["day2_date"])}:
        """
        await state.set_state(FCIStates.waiting_for_day2)
        if callback.message and hasattr(callback.message, "edit_text"):
            await callback.message.edit_text(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
        elif callback.bot:
            await callback.bot.send_message(
                chat_id=callback.from_user.id, text=text, parse_mode="HTML", reply_markup=get_cancel_keyboard()
            )

    elif "day1_value" in data and "day2_value" in data:
        # Нужно ввести данные за day3
        text = f"""
✅ Продолжаем расчёт ФЧИ

Введите количество ультракороткого инсулина за {format_date(data["day3_date"])}:
        """
        await state.set_state(FCIStates.waiting_for_day3)
        if callback.message and hasattr(callback.message, "edit_text"):
            await callback.message.edit_text(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
        elif callback.bot:
            await callback.bot.send_message(
                chat_id=callback.from_user.id, text=text, parse_mode="HTML", reply_markup=get_cancel_keyboard()
            )

    await callback.answer()


@router.callback_query(F.data == "fci_edit_value")
async def start_fci_edit(callback: CallbackQuery, state: FSMContext):
    """Начало изменения данных инсулина для пересчета ФЧИ"""
    await state.set_state(FCIStates.waiting_for_edit_date)

    text = """
✏️ <b>Изменение данных для расчета ФЧИ</b>

Введите дату, за которую хотите изменить количество инсулина, в формате ДД.ММ.ГГГГ (например: 03.10.2024):
    """

    if callback.message and hasattr(callback.message, "edit_text"):
        await callback.message.edit_text(text, parse_mode="HTML", reply_markup=get_cancel_keyboard())
    elif callback.bot:
        await callback.bot.send_message(
            chat_id=callback.from_user.id, text=text, parse_mode="HTML", reply_markup=get_cancel_keyboard()
        )
    await callback.answer()


@router.message(FCIStates.waiting_for_edit_date)
async def process_fci_edit_date(message: Message, state: FSMContext, user):
    """Обработка ввода даты для изменения данных инсулина"""
    try:
        from datetime import datetime

        # Парсим дату
        date_str = (message.text or "").strip()
        date_obj = datetime.strptime(date_str, "%d.%m.%Y").date()

        # Получаем текущее значение инсулина за эту дату
        async with async_session() as session:
            current_insulin = await get_insulin_for_fci(user.id, date_obj, session)

        await state.update_data(edit_date=date_obj, current_insulin=current_insulin)
        await state.set_state(FCIStates.waiting_for_edit_value)

        text = f"""
✅ Дата: {format_date(date_obj)}
💉 Текущее количество инсулина: <b>{current_insulin:.1f} ед.</b>

Введите новое количество ультракороткого инсулина за этот день:
        """

        await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")

    except ValueError:
        await message.answer(
            "❌ Неверный формат даты. Введите дату в формате ДД.ММ.ГГГГ (например: 03.10.2024):",
            reply_markup=get_cancel_keyboard(),
        )


@router.message(FCIStates.waiting_for_edit_value)
async def process_fci_edit_value(message: Message, state: FSMContext, user):
    """Обработка ввода нового количества инсулина и пересчет ФЧИ"""
    try:
        new_insulin = parse_number_input(message.text or "")
        if new_insulin < 0:
            await message.answer(
                "❌ Количество инсулина не может быть отрицательным. Попробуйте ещё раз:",
                reply_markup=get_cancel_keyboard(),
            )
            return

        data = await state.get_data()
        edit_date = data["edit_date"]
        current_insulin = data["current_insulin"]

        # Сохраняем новые данные инсулина как ручную запись
        async with async_session() as session:
            insulin_repo = InsulinRecordRepository(session)
            await insulin_repo.update_or_create_manual(
                user_id=user.id, target_date=edit_date, insulin_type=InsulinType.FOOD, amount=new_insulin
            )

        text = f"""
✅ <b>Данные инсулина изменены!</b>

📅 Дата: {format_date(edit_date)}
💉 Старое значение: {current_insulin:.1f} ед.
💉 Новое значение: <b>{new_insulin:.1f} ед.</b>

Изменения сохранены! Теперь пересчитайте ФЧИ, чтобы обновить его значение.
        """

        await state.clear()
        await message.answer(text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())

    except ValueError:
        await message.answer(
            "❌ Неверный формат числа. Введите количество инсулина числом (например: 12.0):",
            reply_markup=get_cancel_keyboard(),
        )
