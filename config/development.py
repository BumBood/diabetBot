from .base import Settings


class DevelopmentSettings(Settings):
    """Настройки для разработки"""

    debug: bool = True
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "diabet_user"
    postgres_password: str = "diabet_password"
    postgres_db: str = "diabet_bot_dev"
