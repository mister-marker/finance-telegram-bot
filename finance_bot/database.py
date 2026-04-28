from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession
)

from sqlalchemy.orm import DeclarativeBase

# ✅ ВАЖНО — через пакет
from finance_bot.config import settings


# создаем движок БД
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
)


# фабрика сессий
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# базовый класс моделей
class Base(DeclarativeBase):
    pass


# получение сессии
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


# создание таблиц
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)