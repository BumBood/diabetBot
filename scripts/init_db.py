#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных PostgreSQL
Запуск: python scripts/init_db.py
"""

import asyncio
import sys
import os

# Добавляем корневую папку проекта в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import create_async_engine
from config.base import settings
from db.models import Base


async def create_database():
    """Создание базы данных и таблиц"""
    # Подключаемся к PostgreSQL без указания базы данных
    admin_url = f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}@{settings.postgres_host}:{settings.postgres_port}/postgres"

    # Создаём базу данных
    admin_engine = create_async_engine(admin_url, isolation_level="AUTOCOMMIT")

    async with admin_engine.begin() as conn:
        # Проверяем, существует ли база данных
        result = await conn.execute(f"SELECT 1 FROM pg_database WHERE datname = '{settings.postgres_db}'")
        if not result.fetchone():
            await conn.execute(f"CREATE DATABASE {settings.postgres_db}")
            print(f"✅ База данных '{settings.postgres_db}' создана")
        else:
            print(f"ℹ️ База данных '{settings.postgres_db}' уже существует")

    await admin_engine.dispose()

    # Подключаемся к созданной базе данных и создаём таблицы
    database_url = settings.get_database_url()
    engine = create_async_engine(database_url)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Таблицы созданы")

    await engine.dispose()
    print("🎉 Инициализация базы данных завершена!")


if __name__ == "__main__":
    asyncio.run(create_database())
