from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from config.base import settings

# Используем сформированный URL для PostgreSQL
database_url = settings.get_database_url()
engine = create_async_engine(database_url, echo=settings.debug)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with async_session() as session:
        yield session
