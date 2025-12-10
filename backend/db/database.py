"""
Настройка подключения к базе данных
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from backend.config import DATABASE_URL

# Создаем async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Если True - будет логировать все SQL запросы
    future=True,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Создаем фабрику сессий
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base для моделей
Base = declarative_base()


async def get_session() -> AsyncSession:
    """Получить сессию БД"""
    async with async_session_maker() as session:
        yield session


async def init_db():
    """Инициализация БД - создание всех таблиц и миграция данных"""
    # Импортируем модели чтобы они зарегистрировались
    from backend.db.models import User, Transaction, Family, TransactionType
    
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Выполняем миграцию данных если нужно
    from backend.db.migrate import migrate_to_family_wallet
    async with async_session_maker() as session:
        await migrate_to_family_wallet(session)


async def close_db():
    """Закрытие подключения к БД"""
    await engine.dispose()





