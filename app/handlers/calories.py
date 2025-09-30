from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from app.states import CaloriesStates
from app.keyboards import (
    get_calories_gender_keyboard,
    get_calories_activity_keyboard,
)


router = Router()


async def _edit_or_send_callback_text(callback: CallbackQuery, text: str):
    msg = callback.message
    if msg is not None and hasattr(msg, "edit_text"):
        try:
            await msg.edit_text(text)
            return
        except Exception:
            pass
    if msg is not None and hasattr(msg, "answer"):
        try:
            await msg.answer(text)
            return
        except Exception:
            pass
    bot = callback.bot
    if bot is not None:
        await bot.send_message(chat_id=callback.from_user.id, text=text)


def _get_activity_coefficient_from_callback(data: str) -> float:
    if data == "cal_act_male_sedentary":
        return 1.0
    if data == "cal_act_male_low":
        return 1.13
    if data == "cal_act_male_medium":
        return 1.26
    if data == "cal_act_male_high":
        return 1.42
    if data == "cal_act_female_sedentary":
        return 1.0
    if data == "cal_act_female_low":
        return 1.16
    if data == "cal_act_female_medium":
        return 1.31
    if data == "cal_act_female_high":
        return 1.56
    raise ValueError("Unknown activity callback data")


def _calc_metabolic_expenses(age_years: int, age_months: int | None) -> int:
    # 0-3 мес = 175; 4-6 мес = 56; 7-12 мес = 22; 1-8 лет = 20; 9-18 лет = 25
    if age_years == 0:
        months = age_months or 0
        if months <= 3:
            return 175
        if months <= 6:
            return 56
        return 22
    if 1 <= age_years <= 8:
        return 20
    return 25


def _calc_eer(
    gender: str,
    age_years: int,
    weight_kg: float,
    height_cm: float,
    activity_coef: float,
    mr: int,
) -> float:
    height_m = height_cm / 100.0
    if age_years < 3:
        # Для мальчиков и девочек 0-3 года: ОЭП = 89 * вес - 100 + МР
        return 89.0 * weight_kg - 100.0 + mr
    # 3-18: полозависимые формулы
    if gender == "male":
        # ОЭП = 88.5 - 61.9 * возраст + КА * (26.7 * вес + 903 * рост(м)) + МР
        return 88.5 - 61.9 * age_years + activity_coef * (26.7 * weight_kg + 903.0 * height_m) + mr
    # female
    return 135.3 - 30.8 * age_years + activity_coef * (10.0 * weight_kg + 934.0 * height_m) + mr


@router.message(F.text == "🔥 Расчет калорий")
async def calories_entry(message: Message, state: FSMContext):
    await state.clear()
    await state.set_state(CaloriesStates.waiting_for_gender)
    await message.answer(
        "<b>Расчет калорий</b>\n\nВыберите пол:",
        reply_markup=get_calories_gender_keyboard(),
        parse_mode="HTML",
    )


@router.callback_query(CaloriesStates.waiting_for_gender, F.data.in_({"cal_gender_male", "cal_gender_female"}))
async def calories_gender_selected(callback: CallbackQuery, state: FSMContext):
    gender = "male" if callback.data == "cal_gender_male" else "female"
    await state.update_data(gender=gender)
    await state.set_state(CaloriesStates.waiting_for_age_years)
    await _edit_or_send_callback_text(callback, "Укажите возраст в полных годах (0-18):")
    await callback.answer()


@router.message(CaloriesStates.waiting_for_age_years)
async def calories_age_years(message: Message, state: FSMContext):
    text = message.text
    if text is None:
        await message.answer("Нужно целое число лет от 0 до 18.")
        return
    try:
        age_years = int(text.strip())
    except Exception:
        await message.answer("Нужно целое число лет от 0 до 18.")
        return
    if age_years < 0 or age_years > 18:
        await message.answer("Возраст должен быть в диапазоне 0-18 лет.")
        return

    await state.update_data(age_years=age_years)

    if age_years == 0:
        # Нужны месяцы для МР
        await state.set_state(CaloriesStates.waiting_for_metabolic_range)
        await message.answer("Укажите возраст в месяцах (0-12):")
        return

    await state.set_state(CaloriesStates.waiting_for_weight_kg)
    await message.answer("Укажите вес в кг (например, 24.5):")


@router.message(CaloriesStates.waiting_for_metabolic_range)
async def calories_age_months(message: Message, state: FSMContext):
    text = message.text
    if text is None:
        await message.answer("Нужно целое число месяцев от 0 до 12.")
        return
    try:
        age_months = int(text.strip())
    except Exception:
        await message.answer("Нужно целое число месяцев от 0 до 12.")
        return
    if age_months < 0 or age_months > 12:
        await message.answer("Месяцы должны быть в диапазоне 0-12.")
        return

    await state.update_data(age_months=age_months)
    await state.set_state(CaloriesStates.waiting_for_weight_kg)
    await message.answer("Укажите вес в кг (например, 7.8):")


@router.message(CaloriesStates.waiting_for_weight_kg)
async def calories_weight(message: Message, state: FSMContext):
    text = message.text
    if text is None:
        await message.answer("Введите число, например 24.5")
        return
    try:
        weight = float(text.replace(",", ".").strip())
    except Exception:
        await message.answer("Введите число, например 24.5")
        return
    if weight <= 0 or weight > 400:
        await message.answer("Вес вне разумных пределов (0-400 кг). Попробуйте снова.")
        return
    await state.update_data(weight_kg=weight)
    await state.set_state(CaloriesStates.waiting_for_height_cm)
    await message.answer("Укажите рост в сантиметрах (например, 128):")


@router.message(CaloriesStates.waiting_for_height_cm)
async def calories_height(message: Message, state: FSMContext):
    text = message.text
    if text is None:
        await message.answer("Введите число, например 128")
        return
    try:
        height_cm = float(text.replace(",", ".").strip())
    except Exception:
        await message.answer("Введите число, например 128")
        return
    if height_cm <= 30 or height_cm > 220:
        await message.answer("Рост вне разумных пределов (30-220 см). Попробуйте снова.")
        return
    await state.update_data(height_cm=height_cm)

    data = await state.get_data()
    gender = data.get("gender", "male")
    await state.set_state(CaloriesStates.waiting_for_activity)
    await message.answer(
        "Выберите уровень физической активности:",
        reply_markup=get_calories_activity_keyboard(gender),
    )


@router.callback_query(CaloriesStates.waiting_for_activity)
async def calories_activity(callback: CallbackQuery, state: FSMContext):
    if not callback.data:
        await callback.answer()
        return
    try:
        activity_coef = _get_activity_coefficient_from_callback(callback.data)
    except Exception:
        await callback.answer()
        return

    await state.update_data(activity_coef=activity_coef)

    data = await state.get_data()
    gender = data["gender"]
    age_years = int(data["age_years"])
    age_months = int(data.get("age_months") or 0)
    weight_kg = float(data["weight_kg"])
    height_cm = float(data["height_cm"])

    mr = _calc_metabolic_expenses(age_years=age_years, age_months=age_months)
    eer = _calc_eer(
        gender=gender,
        age_years=age_years,
        weight_kg=weight_kg,
        height_cm=height_cm,
        activity_coef=activity_coef,
        mr=mr,
    )

    eer_rounded = int(round(eer))

    # Итог
    lines = [
        "<b>Расчет калорий</b>",
        f"Пол: {'Мальчик' if gender == 'male' else 'Девочка'}",
        f"Возраст: {age_years} лет" + (f" {age_months} мес" if age_years == 0 else ""),
        f"Вес: {weight_kg:.1f} кг",
        f"Рост: {height_cm:.0f} см",
        f"КА: {activity_coef}",
        f"МР: {mr}",
        "",
        f"Оценочная энергетическая потребность: <b>{eer_rounded} ккал/день</b>",
        "",
        "Дальше: учитывайте БЖУ, подбирайте рацион и отслеживайте СК.",
    ]

    # Итоговое сообщение
    text = "\n".join(lines)
    msg = callback.message
    if msg is not None and hasattr(msg, "edit_text"):
        try:
            await msg.edit_text(text, parse_mode="HTML")
            await state.clear()
            await callback.answer()
            return
        except Exception:
            pass
    if msg is not None and hasattr(msg, "answer"):
        try:
            await msg.answer(text, parse_mode="HTML")
            await state.clear()
            await callback.answer()
            return
        except Exception:
            pass
    bot = callback.bot
    if bot is not None:
        await bot.send_message(chat_id=callback.from_user.id, text=text, parse_mode="HTML")
    await state.clear()
    await callback.answer()
