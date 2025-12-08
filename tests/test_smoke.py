"""
Smoke-тесты для проверки базовой работоспособности
"""
import pytest
import asyncio
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from backend.db.models import User, Transaction, TransactionType, Base
from backend.config import DATABASE_URL


# Используем тестовую БД (в реальности нужна отдельная)
TEST_DATABASE_URL = DATABASE_URL.replace('money_bot', 'money_bot_test')


@pytest.fixture(scope='function')
async def test_db_session():
    """Создает тестовую сессию БД"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    
    # Создаем таблицы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Создаем фабрику сессий
    async_session = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    # Возвращаем сессию
    async with async_session() as session:
        yield session
    
    # Удаляем таблицы после теста
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.mark.asyncio
async def test_create_user(test_db_session):
    """Тест создания пользователя"""
    user = User(
        telegram_id=123456789,
        username="test_user",
        first_name="Test",
        last_name="User",
        current_balance=0.0
    )
    
    test_db_session.add(user)
    await test_db_session.commit()
    await test_db_session.refresh(user)
    
    # Проверяем, что пользователь создан
    result = await test_db_session.execute(
        select(User).where(User.telegram_id == 123456789)
    )
    saved_user = result.scalar_one_or_none()
    
    assert saved_user is not None
    assert saved_user.telegram_id == 123456789
    assert saved_user.username == "test_user"
    assert float(saved_user.current_balance) == 0.0


@pytest.mark.asyncio
async def test_income_transaction(test_db_session):
    """Тест создания транзакции пополнения"""
    # Создаем пользователя
    user = User(
        telegram_id=123456789,
        username="test_user",
        current_balance=1000.0
    )
    test_db_session.add(user)
    await test_db_session.commit()
    
    # Создаем транзакцию пополнения
    transaction = Transaction(
        telegram_id=user.telegram_id,
        transaction_type=TransactionType.INCOME,
        amount=500.0,
        description="Test income"
    )
    test_db_session.add(transaction)
    
    # Обновляем баланс пользователя
    user.current_balance = float(user.current_balance) + 500.0
    
    await test_db_session.commit()
    await test_db_session.refresh(user)
    
    # Проверяем баланс
    assert float(user.current_balance) == 1500.0
    
    # Проверяем транзакцию
    result = await test_db_session.execute(
        select(Transaction).where(Transaction.telegram_id == user.telegram_id)
    )
    saved_transaction = result.scalar_one_or_none()
    
    assert saved_transaction is not None
    assert saved_transaction.transaction_type == TransactionType.INCOME
    assert float(saved_transaction.amount) == 500.0


@pytest.mark.asyncio
async def test_expense_transaction(test_db_session):
    """Тест создания транзакции расхода"""
    # Создаем пользователя с балансом
    user = User(
        telegram_id=123456789,
        username="test_user",
        current_balance=1000.0
    )
    test_db_session.add(user)
    await test_db_session.commit()
    
    # Создаем транзакцию расхода
    transaction = Transaction(
        telegram_id=user.telegram_id,
        transaction_type=TransactionType.EXPENSE,
        amount=300.0,
        description="Test expense"
    )
    test_db_session.add(transaction)
    
    # Обновляем баланс пользователя
    user.current_balance = float(user.current_balance) - 300.0
    
    await test_db_session.commit()
    await test_db_session.refresh(user)
    
    # Проверяем баланс
    assert float(user.current_balance) == 700.0
    
    # Проверяем транзакцию
    result = await test_db_session.execute(
        select(Transaction).where(Transaction.telegram_id == user.telegram_id)
    )
    saved_transaction = result.scalar_one_or_none()
    
    assert saved_transaction is not None
    assert saved_transaction.transaction_type == TransactionType.EXPENSE
    assert float(saved_transaction.amount) == 300.0


@pytest.mark.asyncio
async def test_multiple_transactions(test_db_session):
    """Тест множественных транзакций"""
    # Создаем пользователя
    user = User(
        telegram_id=123456789,
        username="test_user",
        current_balance=0.0
    )
    test_db_session.add(user)
    await test_db_session.commit()
    
    # Добавляем пополнение
    income = Transaction(
        telegram_id=user.telegram_id,
        transaction_type=TransactionType.INCOME,
        amount=1000.0
    )
    test_db_session.add(income)
    user.current_balance = float(user.current_balance) + 1000.0
    await test_db_session.commit()
    
    # Добавляем расход
    expense = Transaction(
        telegram_id=user.telegram_id,
        transaction_type=TransactionType.EXPENSE,
        amount=300.0
    )
    test_db_session.add(expense)
    user.current_balance = float(user.current_balance) - 300.0
    await test_db_session.commit()
    
    # Добавляем еще расход
    expense2 = Transaction(
        telegram_id=user.telegram_id,
        transaction_type=TransactionType.EXPENSE,
        amount=200.0
    )
    test_db_session.add(expense2)
    user.current_balance = float(user.current_balance) - 200.0
    await test_db_session.commit()
    
    await test_db_session.refresh(user)
    
    # Проверяем итоговый баланс
    assert float(user.current_balance) == 500.0
    
    # Проверяем количество транзакций
    result = await test_db_session.execute(
        select(Transaction).where(Transaction.telegram_id == user.telegram_id)
    )
    transactions = result.scalars().all()
    
    assert len(transactions) == 3
    assert transactions[0].transaction_type == TransactionType.INCOME
    assert transactions[1].transaction_type == TransactionType.EXPENSE
    assert transactions[2].transaction_type == TransactionType.EXPENSE


@pytest.mark.asyncio
async def test_negative_balance_allowed(test_db_session):
    """Тест, что отрицательный баланс разрешен (можно уйти в минус)"""
    user = User(
        telegram_id=123456789,
        username="test_user",
        current_balance=100.0
    )
    test_db_session.add(user)
    await test_db_session.commit()
    
    # Тратим больше, чем есть
    transaction = Transaction(
        telegram_id=user.telegram_id,
        transaction_type=TransactionType.EXPENSE,
        amount=500.0
    )
    test_db_session.add(transaction)
    user.current_balance = float(user.current_balance) - 500.0
    
    await test_db_session.commit()
    await test_db_session.refresh(user)
    
    # Баланс должен быть отрицательным
    assert float(user.current_balance) == -400.0





