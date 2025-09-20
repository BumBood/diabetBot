from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from app.keyboards import get_main_menu_keyboard

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message):
    """Обработчик команды /start"""
    welcome_text = """
🩺 <b>Добро пожаловать в DiabetBot!</b>

Я помогу вам рассчитать:
• <b>ФЧИ</b> (формула чувствительности к инсулину)
• <b>УК</b> (условный коэффициент для приёмов пищи)

Бот будет собирать данные, выполнять расчёты по формулам, сохранять их и предоставлять историю и прогнозы.

Готовы начать работу? Выберите нужное действие в меню ниже 👇
    """

    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard(), parse_mode="HTML")
