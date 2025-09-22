from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import date
from app.states import MealStates
from app.keyboards import (
    get_meal_type_keyboard,
    get_additional_injection_keyboard,
    get_additional_carbs_keyboard,
    get_time_from_meal_keyboard,
    get_main_menu_keyboard,
    get_cancel_keyboard,
)
from app.utils import (
    parse_glucose_input,
    parse_number_input,
    calculate_uk,
    calculate_injection_correction,
    get_meal_type_name,
)
from db.repository import MealRecordRepository, AdditionalInjectionRepository, FCIRepository, UserRepository
from db.session import async_session
from db.models import MealType

router = Router()


@router.message(F.text == "🍽️ Рассчитать УК")
async def start_uk_calculation(message: Message, state: FSMContext):
    """Начало расчёта УК"""
    text = """
🍽️ <b>Расчёт УК (условный коэффициент)</b>

Выберите приём пищи, для которого хотите рассчитать УК:
    """

    await state.set_state(MealStates.waiting_for_meal_type)
    await message.answer(text, reply_markup=get_meal_type_keyboard(), parse_mode="HTML")


@router.callback_query(F.data.startswith("meal_"))
async def process_meal_type_selection(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа приёма пищи"""
    meal_type_str = callback.data.split("_")[1]
    meal_type = MealType(meal_type_str)

    await state.update_data(meal_type=meal_type)
    await state.set_state(MealStates.waiting_for_glucose_start)

    text = f"""
✅ Выбран: {get_meal_type_name(meal_type)}

📊 <b>Шаг 1:</b> Введите уровень сахара (СК_старт) в ммоль/л на момент ввода инсулина:
    """

    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.message(MealStates.waiting_for_glucose_start)
async def process_glucose_start(message: Message, state: FSMContext, user):
    """Обработка ввода СК_старт"""
    try:
        glucose_start = parse_glucose_input(message.text)
        if glucose_start < 1 or glucose_start > 30:
            await message.answer(
                "❌ Уровень глюкозы должен быть от 1 до 30 ммоль/л. Попробуйте ещё раз:",
                reply_markup=get_cancel_keyboard(),
            )
            return

        await state.update_data(glucose_start=glucose_start)
        await state.set_state(MealStates.waiting_for_pause_time)

        text = f"""
✅ СК_старт: {glucose_start} ммоль/л

⏱️ <b>Шаг 2:</b> Введите время паузы между едой и уколом в минутах (или 0, если уколали сразу):
        """

        await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")

    except ValueError:
        await message.answer(
            "❌ Неверный формат уровня глюкозы. Введите число (например: 7.5):", reply_markup=get_cancel_keyboard()
        )


@router.message(MealStates.waiting_for_pause_time)
async def process_pause_time(message: Message, state: FSMContext, user):
    """Обработка ввода времени паузы"""
    try:
        pause_time = int(parse_number_input(message.text))
        if pause_time < 0:
            await message.answer(
                "❌ Время паузы не может быть отрицательным. Попробуйте ещё раз:", reply_markup=get_cancel_keyboard()
            )
            return

        await state.update_data(pause_time=pause_time)
        await state.set_state(MealStates.waiting_for_carbs_main)

        text = f"""
✅ Время паузы: {pause_time} мин.

🍞 <b>Шаг 3:</b> Введите количество углеводов в граммах:
        """

        await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")

    except ValueError:
        await message.answer("❌ Неверный формат времени. Введите число минут (например: 15):")


@router.message(MealStates.waiting_for_carbs_main)
async def process_carbs_main(message: Message, state: FSMContext, user):
    """Обработка ввода основных углеводов"""
    try:
        carbs_main = parse_number_input(message.text)
        if carbs_main < 0:
            await message.answer(
                "❌ Количество углеводов не может быть отрицательным. Попробуйте ещё раз:",
                reply_markup=get_cancel_keyboard(),
            )
            return

        await state.update_data(carbs_main=carbs_main)
        await state.set_state(MealStates.waiting_for_carbs_additional)

        text = f"""
✅ Основные углеводы: {carbs_main}г

🍭 <b>Шаг 4:</b> Были ли дополнительные углеводы (сладости, соки и т.д.)?
        """

        await message.answer(text, reply_markup=get_additional_carbs_keyboard(), parse_mode="HTML")

    except ValueError:
        await message.answer(
            "❌ Неверный формат числа. Введите количество углеводов (например: 50):",
            reply_markup=get_cancel_keyboard(),
        )


@router.callback_query(F.data == "add_carbs")
async def add_additional_carbs(callback: CallbackQuery, state: FSMContext):
    """Добавление дополнительных углеводов"""
    await state.set_state(MealStates.waiting_for_carbs_additional)

    text = """
🍭 Введите количество дополнительных углеводов в граммах:
    """

    await callback.message.edit_text(text)
    await callback.answer()


@router.callback_query(F.data == "skip_carbs")
async def skip_additional_carbs(callback: CallbackQuery, state: FSMContext):
    """Пропуск дополнительных углеводов"""
    await state.update_data(carbs_additional=0.0)
    await state.set_state(MealStates.waiting_for_proteins)

    text = """
✅ Дополнительные углеводы: 0г

🥩 <b>Шаг 5:</b> Введите количество белков в граммах (или 0, если не считаете):
    """

    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.message(MealStates.waiting_for_carbs_additional)
async def process_carbs_additional(message: Message, state: FSMContext, user):
    """Обработка ввода дополнительных углеводов"""
    try:
        carbs_additional = parse_number_input(message.text)
        if carbs_additional < 0:
            await message.answer(
                "❌ Количество углеводов не может быть отрицательным. Попробуйте ещё раз:",
                reply_markup=get_cancel_keyboard(),
            )
            return

        await state.update_data(carbs_additional=carbs_additional)
        await state.set_state(MealStates.waiting_for_proteins)

        text = f"""
✅ Дополнительные углеводы: {carbs_additional}г

🥩 <b>Шаг 5:</b> Введите количество белков в граммах (или 0, если не считаете):
        """

        await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")

    except ValueError:
        await message.answer(
            "❌ Неверный формат числа. Введите количество углеводов (например: 15):",
            reply_markup=get_cancel_keyboard(),
        )


@router.message(MealStates.waiting_for_proteins)
async def process_proteins(message: Message, state: FSMContext, user):
    """Обработка ввода белков"""
    try:
        proteins = parse_number_input(message.text)
        if proteins < 0:
            await message.answer(
                "❌ Количество белков не может быть отрицательным. Попробуйте ещё раз:",
                reply_markup=get_cancel_keyboard(),
            )
            return

        await state.update_data(proteins=proteins)
        await state.set_state(MealStates.waiting_for_insulin_food)

        text = f"""
✅ Белки: {proteins}г

💉 <b>Шаг 6:</b> Введите количество инсулина на еду в единицах:
        """

        await message.answer(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")

    except ValueError:
        await message.answer(
            "❌ Неверный формат числа. Введите количество белков (например: 20):", reply_markup=get_cancel_keyboard()
        )


@router.message(MealStates.waiting_for_insulin_food)
async def process_insulin_food(message: Message, state: FSMContext, user):
    """Обработка ввода инсулина на еду"""
    try:
        insulin_food = parse_number_input(message.text)
        if insulin_food < 0:
            await message.answer(
                "❌ Количество инсулина не может быть отрицательным. Попробуйте ещё раз:",
                reply_markup=get_cancel_keyboard(),
            )
            return

        await state.update_data(insulin_food=insulin_food)
        await state.set_state(MealStates.waiting_for_additional_injections)

        text = f"""
✅ Инсулин на еду: {insulin_food} ед.

💉 <b>Шаг 7:</b> Были ли дополнительные подколки (коррекции) после еды?
        """

        await message.answer(text, reply_markup=get_additional_injection_keyboard(), parse_mode="HTML")

    except ValueError:
        await message.answer(
            "❌ Неверный формат числа. Введите количество инсулина (например: 5.5):",
            reply_markup=get_cancel_keyboard(),
        )


@router.callback_query(F.data == "add_injection")
async def add_additional_injection(callback: CallbackQuery, state: FSMContext):
    """Добавление дополнительной подколки"""
    await state.update_data(additional_injections=[])
    await state.set_state(MealStates.waiting_for_additional_injections)

    text = """
💉 Выберите время подколки относительно еды:
    """

    await callback.message.edit_text(text, reply_markup=get_time_from_meal_keyboard())
    await callback.answer()


@router.callback_query(F.data.startswith("time_"))
async def process_injection_time(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора времени подколки"""
    time_minutes = int(callback.data.split("_")[1])

    await state.update_data(current_injection_time=time_minutes)
    await state.set_state(MealStates.waiting_for_additional_injections)

    text = f"""
⏱️ Время подколки: {time_minutes // 60} час(ов)

💉 Введите дозу подколки в единицах:
    """

    await callback.message.edit_text(text)
    await callback.answer()


@router.message(MealStates.waiting_for_additional_injections)
async def process_injection_dose(message: Message, state: FSMContext, user):
    """Обработка ввода дозы подколки"""
    try:
        dose = parse_number_input(message.text)
        if dose <= 0:
            await message.answer(
                "❌ Доза должна быть больше 0. Попробуйте ещё раз:", reply_markup=get_cancel_keyboard()
            )
            return

        data = await state.get_data()
        time_minutes = data.get("current_injection_time", 0)

        # Рассчитываем коррекцию
        correction_factor = calculate_injection_correction(time_minutes)
        corrected_dose = dose * correction_factor

        # Добавляем к списку подколок
        injections = data.get("additional_injections", [])
        injections.append({"time": time_minutes, "dose": dose, "corrected_dose": corrected_dose})
        await state.update_data(additional_injections=injections)

        text = f"""
✅ Подколка добавлена:
• Время: {time_minutes // 60} час(ов) после еды
• Доза: {dose} ед.
• С коррекцией: {corrected_dose:.2f} ед.

Добавить ещё одну подколку?
        """

        await message.answer(text, reply_markup=get_additional_injection_keyboard(), parse_mode="HTML")

    except ValueError:
        await message.answer(
            "❌ Неверный формат числа. Введите дозу инсулина (например: 2.5):", reply_markup=get_cancel_keyboard()
        )


@router.callback_query(F.data == "finish_injections")
async def finish_injections(callback: CallbackQuery, state: FSMContext):
    """Завершение ввода подколок"""
    data = await state.get_data()
    injections = data.get("additional_injections", [])

    total_additional_insulin = sum(inj["corrected_dose"] for inj in injections)
    await state.update_data(insulin_additional=total_additional_insulin)
    await state.set_state(MealStates.waiting_for_glucose_end)

    text = f"""
✅ Подколки завершены. Всего дополнительного инсулина: {total_additional_insulin:.2f} ед.

📊 <b>Шаг 8:</b> Введите уровень сахара (СК_отработка) через 4-5 часов после еды в ммоль/л:
    """

    await callback.message.edit_text(text, parse_mode="HTML")
    await callback.answer()


@router.message(MealStates.waiting_for_glucose_end)
async def process_glucose_end(message: Message, state: FSMContext, user):
    """Обработка ввода СК_отработка и финальный расчёт УК"""
    try:
        glucose_end = parse_glucose_input(message.text)
        if glucose_end < 1 or glucose_end > 30:
            await message.answer(
                "❌ Уровень глюкозы должен быть от 1 до 30 ммоль/л. Попробуйте ещё раз:",
                reply_markup=get_cancel_keyboard(),
            )
            return

        data = await state.get_data()

        # Получаем ФЧИ из базы данных
        async with async_session() as session:
            fci_repo = FCIRepository(session)
            latest_fci = await fci_repo.get_latest(user.id)

            if not latest_fci:
                await message.answer(
                    "❌ Сначала нужно рассчитать ФЧИ! Используйте команду '📊 Рассчитать ФЧИ'",
                    reply_markup=get_main_menu_keyboard(),
                )
                await state.clear()
                return

            fci_value = latest_fci.value

            # Рассчитываем УК
            uk_value = calculate_uk(
                glucose_start=data["glucose_start"],
                glucose_end=glucose_end,
                fci=fci_value,
                insulin_food=data["insulin_food"],
                insulin_additional=data.get("insulin_additional", 0),
                carbs_main=data["carbs_main"],
                carbs_additional=data.get("carbs_additional", 0),
            )

            # Сохраняем запись о приёме пищи
            meal_repo = MealRecordRepository(session)
            meal_record = await meal_repo.create(
                user_id=user.id,
                date=date.today(),
                meal_type=data["meal_type"],
                glucose_start=data["glucose_start"],
                pause_time=data.get("pause_time"),
                carbs_main=data["carbs_main"],
                carbs_additional=data.get("carbs_additional", 0),
                proteins=data.get("proteins"),
                insulin_food=data["insulin_food"],
                glucose_end=glucose_end,
                insulin_additional=data.get("insulin_additional", 0),
                uk_value=uk_value,
            )

            # Сохраняем подколки
            if data.get("additional_injections"):
                injection_repo = AdditionalInjectionRepository(session)
                for inj in data["additional_injections"]:
                    await injection_repo.create(
                        meal_record_id=meal_record.id,
                        time_from_meal=inj["time"],
                        dose=inj["dose"],
                        dose_corrected=inj["corrected_dose"],
                    )

        # Формируем результат
        result_text = f"""
🎉 <b>Расчёт УК завершён!</b>

📊 <b>Данные:</b>
• Приём пищи: {get_meal_type_name(data["meal_type"])}
• СК_старт: {data["glucose_start"]} ммоль/л
• СК_отработка: {glucose_end} ммоль/л
• Углеводы: {data["carbs_main"]}г + {data.get("carbs_additional", 0)}г = {data["carbs_main"] + data.get("carbs_additional", 0)}г
• Инсулин на еду: {data["insulin_food"]} ед.
• Дополнительный инсулин: {data.get("insulin_additional", 0):.2f} ед.
• ФЧИ: {fci_value:.2f}

📈 <b>Результат:</b>
• <b>УК = {uk_value:.3f}</b>

Данные сохранены! Теперь вы можете использовать этот УК для планирования следующих приёмов пищи.
        """

        await state.clear()
        await message.answer(result_text, parse_mode="HTML", reply_markup=get_main_menu_keyboard())

    except ValueError:
        await message.answer(
            "❌ Неверный формат уровня глюкозы. Введите число (например: 6.8):", reply_markup=get_cancel_keyboard()
        )
