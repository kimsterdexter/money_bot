FROM python:3.12-slim

# Установка зависимостей системы для компиляции asyncpg
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Создание рабочей директории
WORKDIR /app

# Копирование requirements.txt и установка зависимостей
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Копирование всего кода бота
COPY backend/ /app/backend/

# Переменная окружения для Python
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Healthcheck для проверки что бот работает
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
  CMD python -c "import sys; sys.exit(0)"

# Запуск бота
CMD ["python", "-m", "backend.bot.main"]

