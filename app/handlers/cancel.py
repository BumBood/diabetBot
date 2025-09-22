from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.fsm.context import FSMContext
from app.keyboards import get_main_menu_keyboard

router = Router()


@router.callback_query(F.data == "cancel_input")
async def cancel_input(callback: CallbackQuery, state: FSMContext):
    """Отмена ввода данных"""
    await state.clear()
    await callback.message.answer("❌ Ввод отменён\n👇 Выберите нужное действие в меню ниже", reply_markup=get_main_menu_keyboard())
    await callback.message.delete()
    await callback.answer()
