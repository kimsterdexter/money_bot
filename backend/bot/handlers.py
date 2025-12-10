"""
Обработчики команд и сообщений бота
"""
import logging
import secrets
from datetime import datetime
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import User, Transaction, TransactionType, Family

router = Router()
logger = logging.getLogger(__name__)


class FinanceStates(StatesGroup):
    """Состояния для записи транзакций"""
    waiting_for_income = State()
    waiting_for_expense = State()
    waiting_for_link_code = State()


async def get_or_create_user(session: AsyncSession, message: Message) -> tuple[User, Family]:
    """Получить или создать пользователя и его семью"""
    telegram_id = message.from_user.id
    
    result = await session.execute(
        select(User).where(User.telegram_id == telegram_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        # Создаем новую семью для пользователя
        family = Family(
            name=f"Семья {message.from_user.first_name}",
            current_balance=0.0
        )
        session.add(family)
        await session.flush()
        
        # Создаем пользователя и привязываем к семье
        user = User(
            telegram_id=telegram_id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            family_id=family.id
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        await session.refresh(family)
        logger.info(f"Создан новый пользователь {telegram_id} и семья {family.id}")
    else:
        # Получаем семью пользователя
        result = await session.execute(
            select(Family).where(Family.id == user.family_id)
        )
        family = result.scalar_one()
    
    return user, family


async def get_family_members(session: AsyncSession, family_id: int) -> list[User]:
    """Получить всех членов семьи"""
    result = await session.execute(
        select(User).where(User.family_id == family_id)
    )
    return result.scalars().all()


@router.message(Command("start"))
async def cmd_start(message: Message, session: AsyncSession):
    """Команда /start"""
    user, family = await get_or_create_user(session, message)
    
    # Получаем членов семьи
    family_members = await get_family_members(session, family.id)
    
    if len(family_members) > 1:
        family_info = f"\n👨‍👩‍👧‍👦 Семейный кошелек ({len(family_members)} чел.)"
    else:
        family_info = "\n\nℹ️ Чтобы добавить члена семьи (жену/мужа), используй команду /link"
    
    welcome_text = (
        f"👋 Привет, {message.from_user.first_name}!\n\n"
        "Я бот для учета семейных финансов.{family_info}\n\n"
        "📝 Доступные команды:\n"
        "/income - Записать пополнение счета\n"
        "/expense - Записать расход\n"
        "/balance - Показать текущий баланс\n"
        "/history - История транзакций (последние 10)\n"
        "/family - Участники семьи\n"
        "/link - Привязать члена семьи\n"
        "/help - Справка\n\n"
        f"💰 Семейный баланс: <b>{float(family.current_balance):.2f} ₽</b>"
    ).format(family_info=family_info)
    
    await message.answer(welcome_text, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help"""
    help_text = (
        "ℹ️ Справка по использованию:\n\n"
        "📥 /income - Записать пополнение счета\n"
        "Бот попросит ввести сумму пополнения.\n\n"
        "📤 /expense - Записать расход\n"
        "Бот попросит ввести сумму расхода.\n\n"
        "💰 /balance - Показать семейный баланс\n"
        "Выводит актуальный остаток на счете.\n\n"
        "📊 /history - История транзакций\n"
        "Показывает последние 10 операций всей семьи с указанием кто добавил.\n\n"
        "👨‍👩‍👧‍👦 /family - Участники семьи\n"
        "Показывает список всех членов семьи.\n\n"
        "🔗 /link - Привязать члена семьи\n"
        "Создаёт код для привязки супруга/супруги к общему кошельку.\n\n"
        "❌ /cancel - Отменить текущую операцию\n\n"
        "Я буду присылать тебе ежедневные напоминания:\n"
        "🌅 Утром - записать пополнения\n"
        "🌙 Вечером - записать расходы"
    )
    
    await message.answer(help_text)


@router.message(Command("balance"))
async def cmd_balance(message: Message, session: AsyncSession):
    """Команда /balance - показать семейный баланс"""
    user, family = await get_or_create_user(session, message)
    
    # Получаем членов семьи
    family_members = await get_family_members(session, family.id)
    
    if len(family_members) > 1:
        members_text = f"\n👥 Участников: {len(family_members)}"
    else:
        members_text = ""
    
    balance_emoji = "💰" if family.current_balance >= 0 else "⚠️"
    
    balance_text = (
        f"{balance_emoji} <b>Семейный баланс:</b>\n\n"
        f"<b>{float(family.current_balance):.2f} ₽</b>{members_text}"
    )
    
    await message.answer(balance_text, parse_mode="HTML")


@router.message(Command("family"))
async def cmd_family(message: Message, session: AsyncSession):
    """Команда /family - показать участников семьи"""
    user, family = await get_or_create_user(session, message)
    
    # Получаем всех членов семьи
    family_members = await get_family_members(session, family.id)
    
    family_text = f"👨‍👩‍👧‍👦 <b>Семья \"{family.name}\"</b>\n\n"
    family_text += f"💰 Общий баланс: <b>{float(family.current_balance):.2f} ₽</b>\n\n"
    family_text += "👥 Участники:\n"
    
    for member in family_members:
        name = member.first_name or member.username or f"ID {member.telegram_id}"
        family_text += f"  • {name}"
        if member.telegram_id == user.telegram_id:
            family_text += " (ты)"
        family_text += "\n"
    
    if len(family_members) == 1:
        family_text += "\n💡 Чтобы добавить супруга/супругу, используй /link"
    
    await message.answer(family_text, parse_mode="HTML")


@router.message(Command("link"))
async def cmd_link(message: Message, session: AsyncSession, state: FSMContext):
    """Команда /link - создать код для привязки члена семьи"""
    user, family = await get_or_create_user(session, message)
    
    # Генерируем уникальный код привязки (6 символов)
    link_code = secrets.token_urlsafe(6)[:6].upper()
    
    # Сохраняем код в состояние (живет 10 минут)
    await state.set_state(FinanceStates.waiting_for_link_code)
    await state.update_data(
        link_code=link_code,
        family_id=family.id,
        expires_at=datetime.utcnow().timestamp() + 600  # 10 минут
    )
    
    link_text = (
        f"🔗 <b>Код для привязки к семейному кошельку:</b>\n\n"
        f"<code>{link_code}</code>\n\n"
        f"Супруг/супруга должен:\n"
        f"1. Запустить бота /start\n"
        f"2. Отправить команду /join\n"
        f"3. Ввести этот код: <code>{link_code}</code>\n\n"
        f"⏰ Код действителен 10 минут"
    )
    
    await message.answer(link_text, parse_mode="HTML")
    logger.info(f"User {user.telegram_id} создал код привязки: {link_code}")


@router.message(Command("join"))
async def cmd_join(message: Message, state: FSMContext):
    """Команда /join - начать процесс присоединения к семье"""
    await state.set_state(FinanceStates.waiting_for_link_code)
    
    await message.answer(
        "🔗 Введи код привязки, который получил от супруга/супруги:\n\n"
        "Код выглядит как: ABC123\n"
        "Для отмены: /cancel"
    )


@router.message(StateFilter(FinanceStates.waiting_for_link_code))
async def process_link_code(message: Message, state: FSMContext, session: AsyncSession):
    """Обработка кода привязки"""
    code = message.text.strip().upper()
    
    # Получаем текущего пользователя
    current_user, current_family = await get_or_create_user(session, message)
    
    # Ищем пользователя который создал этот код
    # Проходим по всем активным состояниям (это упрощенная версия)
    # В продакшене лучше хранить коды в БД
    
    # Проверяем данные из state того кто создал код
    data = await state.get_data()
    
    if 'link_code' not in data:
        await message.answer(
            "❌ Код не найден.\n\n"
            "Попроси супруга/супругу отправить команду /link и получить новый код."
        )
        await state.clear()
        return
    
    # Проверяем код
    if data['link_code'] != code:
        await message.answer(
            "❌ Неверный код. Попробуй еще раз или используй /cancel для отмены."
        )
        return
    
    # Проверяем срок действия
    if datetime.utcnow().timestamp() > data.get('expires_at', 0):
        await message.answer(
            "⏰ Код истек (10 минут).\n\n"
            "Попроси супруга/супругу создать новый код через /link"
        )
        await state.clear()
        return
    
    target_family_id = data['family_id']
    
    # Проверяем не пытается ли пользователь привязаться к самому себе
    if current_family.id == target_family_id:
        await message.answer("❌ Это код твоей собственной семьи!")
        await state.clear()
        return
    
    # Получаем целевую семью
    result = await session.execute(
        select(Family).where(Family.id == target_family_id)
    )
    target_family = result.scalar_one()
    
    # Переносим баланс текущей семьи в целевую
    target_family.current_balance = float(target_family.current_balance) + float(current_family.current_balance)
    
    # Переносим все транзакции текущего пользователя
    result = await session.execute(
        select(Transaction).where(Transaction.family_id == current_family.id)
    )
    transactions = result.scalars().all()
    
    for tx in transactions:
        tx.family_id = target_family.id
    
    # Удаляем старую семью (если там только один человек)
    old_family_members = await get_family_members(session, current_family.id)
    
    # Привязываем пользователя к новой семье
    current_user.family_id = target_family.id
    current_user.updated_at = datetime.utcnow()
    
    # Если в старой семье был только этот пользователь - удаляем её
    if len(old_family_members) == 1:
        await session.delete(current_family)
    
    await session.commit()
    await state.clear()
    
    # Уведомляем обоих
    new_members = await get_family_members(session, target_family.id)
    
    await message.answer(
        f"✅ Успешно привязан к семье!\n\n"
        f"👨‍👩‍👧‍👦 Теперь в семье {len(new_members)} чел.\n"
        f"💰 Общий баланс: <b>{float(target_family.current_balance):.2f} ₽</b>",
        parse_mode="HTML"
    )
    
    logger.info(f"User {current_user.telegram_id} присоединился к семье {target_family.id}")


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
        
        user, family = await get_or_create_user(session, message)
        
        # Имя пользователя для отображения
        user_display_name = user.first_name or user.username or f"ID {user.telegram_id}"
        
        # Создаем транзакцию
        transaction = Transaction(
            family_id=family.id,
            telegram_id=user.telegram_id,
            user_name=user_display_name,
            transaction_type=TransactionType.INCOME,
            amount=amount,
            description="Пополнение",
            created_at=datetime.utcnow()
        )
        session.add(transaction)
        
        # Обновляем баланс СЕМЬИ
        family.current_balance = float(family.current_balance) + amount
        family.updated_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(family)
        
        await message.answer(
            f"✅ Пополнение записано!\n\n"
            f"💵 +{amount:.2f} ₽ (добавил: {user_display_name})\n"
            f"💰 Семейный баланс: <b>{float(family.current_balance):.2f} ₽</b>",
            parse_mode="HTML"
        )
        
        await state.clear()
        logger.info(f"User {user.telegram_id} добавил пополнение {amount} в семью {family.id}")
        
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
        
        user, family = await get_or_create_user(session, message)
        
        # Имя пользователя для отображения
        user_display_name = user.first_name or user.username or f"ID {user.telegram_id}"
        
        # Создаем транзакцию
        transaction = Transaction(
            family_id=family.id,
            telegram_id=user.telegram_id,
            user_name=user_display_name,
            transaction_type=TransactionType.EXPENSE,
            amount=amount,
            description="Расход",
            created_at=datetime.utcnow()
        )
        session.add(transaction)
        
        # Обновляем баланс СЕМЬИ
        family.current_balance = float(family.current_balance) - amount
        family.updated_at = datetime.utcnow()
        
        await session.commit()
        await session.refresh(family)
        
        balance_emoji = "💰" if family.current_balance >= 0 else "⚠️"
        
        await message.answer(
            f"✅ Расход записан!\n\n"
            f"💸 -{amount:.2f} ₽ (добавил: {user_display_name})\n"
            f"{balance_emoji} Семейный баланс: <b>{float(family.current_balance):.2f} ₽</b>",
            parse_mode="HTML"
        )
        
        await state.clear()
        logger.info(f"User {user.telegram_id} добавил расход {amount} в семью {family.id}")
        
    except ValueError:
        await message.answer(
            "❌ Не могу распознать сумму. Введи число, например: 500 или 299.99"
        )


@router.message(Command("history"))
async def cmd_history(message: Message, session: AsyncSession):
    """Команда /history - показать историю транзакций семьи"""
    user, family = await get_or_create_user(session, message)
    
    # Получаем последние 10 транзакций СЕМЬИ
    result = await session.execute(
        select(Transaction)
        .where(Transaction.family_id == family.id)
        .order_by(Transaction.created_at.desc())
        .limit(10)
    )
    transactions = result.scalars().all()
    
    if not transactions:
        await message.answer("📊 История транзакций пуста")
        return
    
    # Получаем членов семьи для отображения
    family_members = await get_family_members(session, family.id)
    
    history_text = "📊 <b>История семейных операций (последние 10):</b>\n\n"
    
    for tx in transactions:
        date_str = tx.created_at.strftime("%d.%m.%Y %H:%M")
        
        if tx.transaction_type == TransactionType.INCOME:
            emoji = "💵"
            sign = "+"
        else:
            emoji = "💸"
            sign = "-"
        
        # Показываем кто добавил (если больше 1 члена семьи)
        if len(family_members) > 1:
            who_added = f" ({tx.user_name})"
        else:
            who_added = ""
        
        history_text += (
            f"{emoji} {sign}{float(tx.amount):.2f} ₽{who_added}\n"
            f"   📅 {date_str}\n\n"
        )
    
    history_text += f"💰 <b>Семейный баланс: {float(family.current_balance):.2f} ₽</b>"
    
    await message.answer(history_text, parse_mode="HTML")
