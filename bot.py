from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config.base import settings
from app.handlers import start, fci, meal, statistics, cancel
from app.handlers import calories
from app.middlewares.user_middleware import UserMiddleware
from db.models import Base
from db.session import engine
import asyncio
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


async def create_tables():
    """Создание таблиц в базе данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Таблицы базы данных созданы")


async def main():
    """Основная функция запуска бота"""
    # Создаём бота и диспетчер
    bot = Bot(token=settings.bot_token)
    dp = Dispatcher(storage=MemoryStorage())

    # Добавляем middleware
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())

    # Создаём таблицы
    await create_tables()

    # Регистрируем роутеры
    dp.include_router(cancel.router)  # Общий обработчик отмены должен быть первым
    dp.include_router(start.router)
    dp.include_router(fci.router)
    dp.include_router(meal.router)
    dp.include_router(statistics.router)
    dp.include_router(calories.router)

    logger.info("Бот запущен")

    try:
        # Запускаем бота
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
