from .base import Settings


class ProductionSettings(Settings):
    """Настройки для продакшена"""

    debug: bool = False
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_user: str = "diabet_user"
    postgres_password: str = "secure_password"
    postgres_db: str = "diabet_bot_prod"
