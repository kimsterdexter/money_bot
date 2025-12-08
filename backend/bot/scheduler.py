"""
Планировщик ежедневных напоминаний
"""
import logging
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import DAILY_INCOME_TIME, DAILY_EXPENSE_TIME, TIMEZONE
from backend.db.models import User
from backend.db.database import async_session_maker

logger = logging.getLogger(__name__)


class ReminderScheduler:
    """Планировщик напоминаний"""
    
    def __init__(self, bot: Bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler(timezone=TIMEZONE)
    
    def start(self):
        """Запустить планировщик"""
        # Парсим время
        income_hour, income_minute = map(int, DAILY_INCOME_TIME.split(':'))
        expense_hour, expense_minute = map(int, DAILY_EXPENSE_TIME.split(':'))
        
        # Добавляем задачи
        self.scheduler.add_job(
            self.send_income_reminder,
            trigger=CronTrigger(hour=income_hour, minute=income_minute, timezone=TIMEZONE),
            id='income_reminder',
            name='Daily Income Reminder',
            replace_existing=True
        )
        
        self.scheduler.add_job(
            self.send_expense_reminder,
            trigger=CronTrigger(hour=expense_hour, minute=expense_minute, timezone=TIMEZONE),
            id='expense_reminder',
            name='Daily Expense Reminder',
            replace_existing=True
        )
        
        self.scheduler.start()
        logger.info(
            f"Планировщик запущен. Напоминания: "
            f"пополнения в {DAILY_INCOME_TIME}, расходы в {DAILY_EXPENSE_TIME}"
        )
    
    def stop(self):
        """Остановить планировщик"""
        self.scheduler.shutdown()
        logger.info("Планировщик остановлен")
    
    async def send_income_reminder(self):
        """Отправить напоминание о записи пополнений"""
        logger.info("Отправка напоминаний о пополнениях...")
        
        async with async_session_maker() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            
            for user in users:
                try:
                    message_text = (
                        "🌅 Доброе утро!\n\n"
                        "Были ли вчера пополнения счета?\n\n"
                        "Если да - используй команду /income\n"
                        "Если нет - можешь пропустить это напоминание"
                    )
                    
                    await self.bot.send_message(
                        chat_id=user.telegram_id,
                        text=message_text
                    )
                    
                    logger.debug(f"Напоминание о пополнении отправлено пользователю {user.telegram_id}")
                    
                except Exception as e:
                    logger.error(f"Ошибка отправки напоминания пользователю {user.telegram_id}: {e}")
    
    async def send_expense_reminder(self):
        """Отправить напоминание о записи расходов"""
        logger.info("Отправка напоминаний о расходах...")
        
        async with async_session_maker() as session:
            result = await session.execute(select(User))
            users = result.scalars().all()
            
            for user in users:
                try:
                    message_text = (
                        "🌙 Добрый вечер!\n\n"
                        "Сколько потратил сегодня?\n\n"
                        "Запиши расходы с помощью команды /expense\n\n"
                        f"💰 Текущий баланс: <b>{float(user.current_balance):.2f} ₽</b>"
                    )
                    
                    await self.bot.send_message(
                        chat_id=user.telegram_id,
                        text=message_text,
                        parse_mode="HTML"
                    )
                    
                    logger.debug(f"Напоминание о расходах отправлено пользователю {user.telegram_id}")
                    
                except Exception as e:
                    logger.error(f"Ошибка отправки напоминания пользователю {user.telegram_id}: {e}")





