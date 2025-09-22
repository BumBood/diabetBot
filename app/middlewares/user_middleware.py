from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
from db.repository import UserRepository
from db.session import async_session


class UserMiddleware(BaseMiddleware):
    """Middleware для автоматического создания пользователей"""

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        # Получаем пользователя из события
        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user
        else:
            return await handler(event, data)

        if not user:
            return await handler(event, data)

        # Создаём или получаем пользователя
        async with async_session() as session:
            user_repo = UserRepository(session)
            db_user = await user_repo.get_or_create(
                telegram_id=user.id, username=user.username, first_name=user.first_name, last_name=user.last_name
            )

            # Добавляем пользователя в данные для хендлеров
            data["user"] = db_user

        return await handler(event, data)


