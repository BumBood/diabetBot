from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    bot_token: str
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/diabet_bot"
    debug: bool = True

    # PostgreSQL настройки
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "user"
    postgres_password: str = "password"
    postgres_db: str = "diabet_bot"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    def get_database_url(self) -> str:
        """Формирует URL для подключения к PostgreSQL"""
        return f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"


settings = Settings()
