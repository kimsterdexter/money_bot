"""
Скрипт миграции БД для семейного кошелька
"""
import logging
from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def migrate_to_family_wallet(session: AsyncSession):
    """
    Миграция БД из личных кошельков в семейные.
    
    Выполняет:
    1. Создание таблицы families (если не существует)
    2. Добавление family_id в users
    3. Создание семьи для каждого пользователя
    4. Перенос балансов из users в families
    5. Обновление transactions (добавление family_id, user_name)
    """
    
    logger.info("Начало миграции БД...")
    
    try:
        # Проверяем существует ли таблица families
        result = await session.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'families'
                )
            """)
        )
        families_exists = result.scalar()
        
        if families_exists:
            logger.info("Таблица families уже существует, проверяем нужна ли миграция данных...")
            
            # Проверяем есть ли пользователи без family_id
            result = await session.execute(
                text("SELECT COUNT(*) FROM users WHERE family_id IS NULL")
            )
            users_without_family = result.scalar()
            
            if users_without_family == 0:
                logger.info("Миграция не требуется, все пользователи уже привязаны к семьям")
                return
            
            logger.info(f"Найдено {users_without_family} пользователей без семьи, выполняем миграцию...")
        
        # Шаг 1: Создаем семьи для существующих пользователей
        logger.info("Создание семей для существующих пользователей...")
        
        # Получаем пользователей без семьи
        result = await session.execute(
            text("""
                SELECT telegram_id, username, first_name, last_name, current_balance 
                FROM users 
                WHERE family_id IS NULL
            """)
        )
        users = result.fetchall()
        
        if not users:
            logger.info("Нет пользователей для миграции")
            return
        
        logger.info(f"Найдено {len(users)} пользователей для миграции")
        
        # Для каждого пользователя создаем семью
        for user in users:
            telegram_id, username, first_name, last_name, current_balance = user
            
            # Создаем семью
            family_name = f"Семья {first_name or username or telegram_id}"
            
            result = await session.execute(
                text("""
                    INSERT INTO families (name, current_balance, created_at, updated_at)
                    VALUES (:name, :balance, NOW(), NOW())
                    RETURNING id
                """),
                {
                    "name": family_name,
                    "balance": current_balance or 0.0
                }
            )
            family_id = result.scalar()
            
            # Привязываем пользователя к семье
            await session.execute(
                text("""
                    UPDATE users 
                    SET family_id = :family_id, updated_at = NOW()
                    WHERE telegram_id = :telegram_id
                """),
                {
                    "family_id": family_id,
                    "telegram_id": telegram_id
                }
            )
            
            logger.info(f"Создана семья {family_id} для пользователя {telegram_id}")
        
        # Шаг 2: Обновляем транзакции - добавляем family_id и user_name
        logger.info("Обновление транзакций...")
        
        # Проверяем есть ли колонка user_name
        result = await session.execute(
            text("""
                SELECT EXISTS (
                    SELECT FROM information_schema.columns 
                    WHERE table_name = 'transactions' 
                    AND column_name = 'user_name'
                )
            """)
        )
        user_name_exists = result.scalar()
        
        if not user_name_exists:
            # Добавляем колонку user_name
            await session.execute(
                text("ALTER TABLE transactions ADD COLUMN IF NOT EXISTS user_name VARCHAR(255)")
            )
            logger.info("Добавлена колонка user_name в transactions")
        
        # Обновляем транзакции: добавляем family_id и user_name из users
        await session.execute(
            text("""
                UPDATE transactions t
                SET 
                    family_id = u.family_id,
                    user_name = COALESCE(u.first_name, u.username, CAST(u.telegram_id AS VARCHAR))
                FROM users u
                WHERE t.telegram_id = u.telegram_id
                AND t.family_id IS NULL
            """)
        )
        
        # Проверяем сколько транзакций обновлено
        result = await session.execute(
            text("SELECT COUNT(*) FROM transactions WHERE family_id IS NOT NULL")
        )
        updated_count = result.scalar()
        
        logger.info(f"Обновлено транзакций: {updated_count}")
        
        # Шаг 3: Удаляем колонку current_balance из users (опционально)
        # Это можно не делать для обратной совместимости
        # Но можно раскомментировать если нужно:
        # await session.execute(
        #     text("ALTER TABLE users DROP COLUMN IF EXISTS current_balance")
        # )
        # logger.info("Удалена колонка current_balance из users")
        
        await session.commit()
        logger.info("✅ Миграция БД успешно завершена!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка миграции БД: {e}")
        await session.rollback()
        raise

