"""
Главный файл бота
"""
import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from backend.config import BOT_TOKEN
from backend.db.database import init_db, close_db, async_session_maker
from backend.bot.handlers import router
from backend.bot.scheduler import ReminderScheduler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


async def session_middleware(handler, event, data):
    """Middleware для добавления сессии БД в handler"""
    async with async_session_maker() as session:
        data['session'] = session
        return await handler(event, data)


async def main():
    """Главная функция запуска бота"""
    logger.info("Запуск бота...")
    
    # Инициализация БД
    try:
        await init_db()
        logger.info("База данных инициализирована")
    except Exception as e:
        logger.error(f"Ошибка инициализации БД: {e}")
        sys.exit(1)
    
    # Инициализация бота и диспетчера
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрация middleware для БД
    dp.message.middleware(session_middleware)
    
    # Регистрация роутера
    dp.include_router(router)
    
    # Запуск планировщика напоминаний
    scheduler = ReminderScheduler(bot)
    scheduler.start()
    
    logger.info("Бот запущен и готов к работе!")
    
    try:
        # Запуск polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        # Graceful shutdown
        logger.info("Остановка бота...")
        scheduler.stop()
        await close_db()
        await bot.session.close()
        logger.info("Бот остановлен")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")

