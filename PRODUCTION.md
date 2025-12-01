# 🏭 Production Deploy Guide

Руководство по деплою Money Bot на продакшен-сервер.

---

## 📋 Предварительные требования

- Ubuntu/Debian сервер (VPS)
- Docker и Docker Compose установлены
- Доступ по SSH
- Telegram Bot Token

---

## 🚀 Быстрый деплой

### 1. Подключись к серверу

```bash
ssh user@your-server.com
```

### 2. Установи Docker (если не установлен)

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo apt install docker-compose -y

# Добавление пользователя в группу docker
sudo usermod -aG docker $USER

# Перелогинься или выполни
newgrp docker
```

### 3. Клонируй репозиторий

```bash
cd ~
git clone <your-repo-url> money_bot
cd money_bot
```

### 4. Настрой .env

```bash
cp env.example .env
nano .env  # или vim .env
```

Укажи свои значения:
```env
BOT_TOKEN=your_actual_bot_token_here
DB_PASSWORD=strong_password_here  # ОБЯЗАТЕЛЬНО смени пароль БД!
DAILY_INCOME_TIME=09:00
DAILY_EXPENSE_TIME=20:00
TIMEZONE=Europe/Moscow  # Твоя таймзона
```

### 5. Запусти деплой

```bash
./deploy.sh
```

Бот запущен! 🎉

---

## 🔧 Автозапуск при перезагрузке сервера

Docker Compose уже настроен на автозапуск (`restart: unless-stopped`).

Контейнеры автоматически запустятся после перезагрузки сервера.

---

## 📊 Мониторинг

### Проверка статуса

```bash
# Статус контейнеров
docker-compose ps

# Логи бота (live)
docker-compose logs -f bot

# Логи БД
docker-compose logs -f postgres

# Использование ресурсов
docker stats
```

### Проверка здоровья БД

```bash
docker exec money_bot_db pg_isready -U postgres
```

---

## 🔄 Обновление бота

### Автоматическое обновление

```bash
git pull
./deploy.sh
```

### Ручное обновление

```bash
# Получить последние изменения
git pull

# Пересобрать и перезапустить
docker-compose down
docker-compose up -d --build
```

---

## 💾 Резервное копирование

### Автоматический бэкап БД (рекомендуется)

Создай скрипт `/home/user/backup_db.sh`:

```bash
#!/bin/bash

BACKUP_DIR="/home/user/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/money_bot_$DATE.sql"

# Создай директорию если нет
mkdir -p $BACKUP_DIR

# Бэкап
docker exec money_bot_db pg_dump -U postgres money_bot > $BACKUP_FILE

# Сжатие
gzip $BACKUP_FILE

# Удаление старых бэкапов (старше 30 дней)
find $BACKUP_DIR -name "money_bot_*.sql.gz" -mtime +30 -delete

echo "Backup created: ${BACKUP_FILE}.gz"
```

Сделай исполняемым:
```bash
chmod +x /home/user/backup_db.sh
```

Добавь в crontab (раз в день в 3:00):
```bash
crontab -e

# Добавь строку:
0 3 * * * /home/user/backup_db.sh >> /home/user/backup.log 2>&1
```

### Ручной бэкап

```bash
# Экспорт БД
docker exec money_bot_db pg_dump -U postgres money_bot > backup.sql

# Или с сжатием
docker exec money_bot_db pg_dump -U postgres money_bot | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Восстановление из бэкапа

```bash
# Из несжатого файла
cat backup.sql | docker exec -i money_bot_db psql -U postgres -d money_bot

# Из сжатого файла
gunzip -c backup_20241201.sql.gz | docker exec -i money_bot_db psql -U postgres -d money_bot
```

---

## 🔒 Безопасность

### 1. Смени пароль БД

В `.env`:
```env
DB_PASSWORD=very_strong_password_123!@#
```

После изменения:
```bash
docker-compose down -v  # ВНИМАНИЕ: удалит данные!
docker-compose up -d --build
```

### 2. Закрой порты

Убери проброс порта PostgreSQL в `docker-compose.yml`:

```yaml
postgres:
  # ports:  # Закомментируй эту секцию
  #   - "5432:5432"
```

БД будет доступна только внутри Docker-сети.

### 3. Настрой firewall

```bash
# Разрешить только SSH
sudo ufw allow 22/tcp
sudo ufw enable
```

### 4. Используй secrets для токена (опционально)

Вместо `.env` можно использовать Docker secrets.

---

## 📈 Масштабирование

### Если нужно обслуживать много пользователей:

1. **Увеличь ресурсы БД** в `docker-compose.yml`:

```yaml
postgres:
  deploy:
    resources:
      limits:
        cpus: '2'
        memory: 2G
```

2. **Настрой connection pooling** в `backend/db/database.py`:

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,      # Увеличь
    max_overflow=40    # Увеличь
)
```

3. **Используй webhook вместо polling** (быстрее для большого количества пользователей)

---

## 🚨 Troubleshooting на продакшене

### Бот перестал отвечать

```bash
# Проверь логи
docker-compose logs --tail=100 bot

# Перезапусти бота
docker-compose restart bot
```

### Нехватка места на диске

```bash
# Проверь использование
df -h

# Очисти старые образы Docker
docker system prune -a

# Очисти логи
docker-compose logs --tail=0 bot > /dev/null
```

### Высокая нагрузка на БД

```bash
# Подключись к БД
docker exec -it money_bot_db psql -U postgres -d money_bot

# Проверь размер таблиц
SELECT 
  schemaname,
  tablename,
  pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Проверь количество записей
SELECT COUNT(*) FROM transactions;
SELECT COUNT(*) FROM users;
```

### Бот не отправляет напоминания

```bash
# Проверь таймзону контейнера
docker exec money_bot date

# Проверь логи планировщика
docker-compose logs bot | grep -i scheduler

# Проверь настройки в .env
cat .env | grep DAILY
```

---

## 📞 Мониторинг алертов (опционально)

Можно добавить интеграцию с:
- **Sentry** - для отслеживания ошибок
- **Prometheus + Grafana** - для метрик
- **Healthchecks.io** - для проверки что бот жив

---

## ✅ Чеклист продакшен-готовности

- [ ] Сильный пароль БД установлен
- [ ] Порт PostgreSQL не открыт наружу
- [ ] Firewall настроен
- [ ] Автоматический бэкап настроен
- [ ] Логи ротируются (уже настроено в docker-compose)
- [ ] Мониторинг настроен
- [ ] `.env` в `.gitignore` (уже есть)
- [ ] Таймзона правильная
- [ ] Тестовые уведомления работают

---

## 🎯 Production-ready конфигурация

Пример `.env` для продакшена:

```env
# Bot
BOT_TOKEN=1234567890:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw

# Database (СИЛЬНЫЕ ПАРОЛИ!)
DB_HOST=postgres
DB_PORT=5432
DB_NAME=money_bot
DB_USER=postgres
DB_PASSWORD=Str0ng_P@ssw0rd_H3r3!

# Schedule (под свою таймзону)
DAILY_INCOME_TIME=09:00
DAILY_EXPENSE_TIME=21:00
TIMEZONE=Europe/Moscow
```

---

## 📚 Дополнительные ресурсы

- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)
- [Telegram Bot API](https://core.telegram.org/bots/api)

---

**Готово!** Бот работает на продакшене 🚀

