"""
Конфигурация бота
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем .env из корня проекта
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Telegram Bot Token
BOT_TOKEN = os.getenv('BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в .env файле")

# Database
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'money_bot')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# Время ежедневных напоминаний (формат HH:MM)
DAILY_INCOME_TIME = os.getenv('DAILY_INCOME_TIME', '09:00')  # Утром спрашиваем про пополнение
DAILY_EXPENSE_TIME = os.getenv('DAILY_EXPENSE_TIME', '20:00')  # Вечером спрашиваем про расходы

# Timezone
TIMEZONE = os.getenv('TIMEZONE', 'Europe/Moscow')

