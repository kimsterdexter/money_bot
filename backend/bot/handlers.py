"""
Обработчики команд и сообщений бота
"""
import logging
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import User, Transaction, TransactionType

router = Router()
logger = logging.getLogger(__name__)


class FinanceStates(StatesGroup):
    """Состояния для записи транзакций"""
    waiting_for_income = State()
    waiting_for_expense = State()


async def get_or_create_user(session: AsyncSession, message: Message) -> User:
    """Получить или создать пользователя"""
    telegram_id = message.from_user.id
    
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            current_balance=0.0
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        logger.info(f"Создан новый пользователь: {telegram_id}")
    
    return user


@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession):
    """Команда /start"""
    user = await get_or_create_user(session, message)
    
    welcome_text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я бот для учета твоих финансов.\n\n"
        "📝 Доступные команды:\n"
        "/income - Записать пополнение счета\n"
        "/expense - Записать расход\n"
        "/balance - Показать текущий баланс\n"
        "/history - История транзакций (последние 10)\n"
        "/help - Справка\n\n"
        f"💰 Твой текущий баланс: {float(user.current_balance):.2f} ₽"
    )
    
    await message.answer(welcome_text)


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help"""
    help_text = (
        "ℹ️ Справка по использованию:\n\n"
        "📥 /income - Записать пополнение счета\n"
        "Бот попросит ввести сумму пополнения.\n\n"
        "📤 /expense - Записать расход\n"
        "Бот попросит ввести сумму расхода.\n\n"
        "💰 /balance - Показать текущий баланс\n"
        "Выводит актуальный остаток на счете.\n\n"
        "📊 /history - История транзакций\n"
        "Показывает последние 10 операций.\n\n"
        "❌ /cancel - Отменить текущую операцию\n\n"
        "Я буду присылать тебе ежедневные напоминания:\n"
        "🌅 Утром - записать пополнения\n"
        "🌙 Вечером - записать расходы"
    )
    
    await message.answer(help_text)


@router.message(Command("balance"))
async def cmd_balance(message: Message, session: AsyncSession):
    """Команда /balance - показать баланс"""
    user = await get_or_create_user(session, message)
    
    balance_text = (
        f"💰 Твой текущий баланс:\n\n"
        f"<b>{float(user.current_balance):.2f} ₽</b>"
    )
    
    await message.answer(balance_text, parse_mode="HTML")


@router.message(Command("income"))
async def cmd_income(message: Message, state: FSMContext):
    """Команда /income - начать запись пополнения"""
    await state.set_state(FinanceStates.waiting_for_income)
    await message.answer(
        "💵 Введи сумму пополнения счета:\n\n"
        "Например: 5000 или 1500.50\n"
        "Для отмены введи /cancel"
    )


@router.message(Command("expense"))
async def cmd_expense(message: Message, state: FSMContext):
    """Команда /expense - начать запись расхода"""
    await state.set_state(FinanceStates.waiting_for_expense)
    await message.answer(
        "💸 Введи сумму расхода:\n\n"
        "Например: 350 или 1299.99\n"
        "Для отмены введи /cancel"
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Команда /cancel - отменить операцию"""
    current_state = await state.get_state()
    
    if current_state is None:
        await message.answer("Нечего отменять 🤷")
        return
    
    await state.clear()
    await message.answer("❌ Операция отменена")


@router.message(StateFilter(FinanceStates.waiting_for_income))
async def process_income(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка суммы пополнения"""
    try:
        amount = float(message.text.replace(',', '.').strip())
        
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше нуля. Попробуй еще раз:")
            return
        
        if amount > 999999999:
            await message.answer("❌ Сумма слишком большая. Попробуй еще раз:")
            return
        
        user = await get_or_create_user(session, message)
        
        # Создаем транзакцию
        transaction = Transaction(
            telegram_id=user.telegram_id,
            transaction_type=TransactionType.INCOME,
            amount=amount,
            description="Пополнение",
            created_at=datetime.utcnow()
        )
        session.add(transaction)
        
        # Обновляем баланс
        user.current_balance = float(user.current_balance) + amount
        user.updated_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(user)
        
        await message.answer(
            f"✅ Пополнение записано!\n\n"
            f"💵 +{amount:.2f} ₽\n"
            f"💰 Новый баланс: <b>{float(user.current_balance):.2f} ₽</b>",
            parse_mode="HTML"
        )
        
        await state.clear()
        logger.info(f"User {user.telegram_id} добавил пополнение {amount}")
        
    except ValueError:
        await message.answer(
            "❌ Не могу распознать сумму. Введи число, например: 1000 или 1500.50"
        )


@router.message(StateFilter(FinanceStates.waiting_for_expense))
async def process_expense(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка суммы расхода"""
    try:
        amount = float(message.text.replace(',', '.').strip())
        
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше нуля. Попробуй еще раз:")
            return
        
        if amount > 999999999:
            await message.answer("❌ Сумма слишком большая. Попробуй еще раз:")
            return
        
        user = await get_or_create_user(session, message)
        
        # Создаем транзакцию
        transaction = Transaction(
            telegram_id=user.telegram_id,
            transaction_type=TransactionType.EXPENSE,
            amount=amount,
            description="Расход",
            created_at=datetime.utcnow()
        )
        session.add(transaction)
        
        # Обновляем баланс
        user.current_balance = float(user.current_balance) - amount
        user.updated_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(user)
        
        balance_emoji = "💰" if user.current_balance >= 0 else "⚠️"
        
        await message.answer(
            f"✅ Расход записан!\n\n"
            f"💸 -{amount:.2f} ₽\n"
            f"{balance_emoji} Новый баланс: <b>{float(user.current_balance):.2f} ₽</b>",
            parse_mode="HTML"
        )
        
        await state.clear()
        logger.info(f"User {user.telegram_id} добавил расход {amount}")
        
    except ValueError:
        await message.answer(
            "❌ Не могу распознать сумму. Введи число, например: 500 или 299.99"
        )


@router.message(Command("history"))
async def cmd_history(message: Message, session: AsyncSession):
    """Команда /history - показать историю транзакций"""
    user = await get_or_create_user(session, message)
    
    # Получаем последние 10 транзакций
    result = await session.execute(
        select(Transaction)
        .where(Transaction.telegram_id == user.telegram_id)
        .order_by(Transaction.created_at.desc())
        .limit(10)
    )
    transactions = result.scalars().all()
    
    if not transactions:
        await message.answer("📊 История транзакций пуста")
        return
    
    history_text = "📊 <b>История операций (последние 10):</b>\n\n"
    
    for tx in transactions:
        date_str = tx.created_at.strftime("%d.%m.%Y %H:%M")
        
        if tx.transaction_type == TransactionType.INCOME:
            emoji = "💵"
            sign = "+"
        else:
            emoji = "💸"
            sign = "-"
        
        history_text += (
            f"{emoji} {sign}{float(tx.amount):.2f} ₽\n"
            f"   📅 {date_str}\n\n"
        )
    
    history_text += f"💰 <b>Текущий баланс: {float(user.current_balance):.2f} ₽</b>"
    
    await message.answer(history_text, parse_mode="HTML")

