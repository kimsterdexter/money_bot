#!/bin/bash

# Скрипт для запуска тестов

echo "🧪 Запуск smoke-тестов..."
echo ""

# Проверяем, что venv активирован
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Виртуальное окружение не активировано!"
    echo "Запусти: source venv/bin/activate"
    exit 1
fi

# Проверяем, что PostgreSQL запущен
if ! docker ps | grep -q money_bot_db; then
    echo "⚠️  PostgreSQL не запущен!"
    echo "Запусти: docker-compose up -d"
    exit 1
fi

# Создаем тестовую БД если её нет
echo "📦 Создание тестовой БД..."
docker exec -i money_bot_db psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'money_bot_test'" | grep -q 1 || \
docker exec -i money_bot_db psql -U postgres -c "CREATE DATABASE money_bot_test;"

echo ""
echo "🚀 Запускаем тесты..."
echo ""

# Запускаем pytest
PYTHONPATH=. pytest tests/ -v --tb=short

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Все тесты прошли успешно!"
else
    echo ""
    echo "❌ Некоторые тесты провалились"
    exit 1
fi

