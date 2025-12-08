# 🐳 Docker Guide - Money Bot

Полное руководство по работе с Docker для Money Bot.

---

## 🎯 Преимущества Docker

✅ **Одна команда** - запуск бота и БД  
✅ **Изоляция** - не нужно ставить Python, PostgreSQL локально  
✅ **Консистентность** - одинаково работает везде (Mac, Linux, Windows)  
✅ **Продакшен-ready** - легко деплоить на сервер  

---

## 📦 Структура

- **`Dockerfile`** - образ бота (Python 3.13 + зависимости)
- **`docker-compose.yml`** - оркестрация (бот + PostgreSQL)
- **`.dockerignore`** - исключения при сборке

---

## 🚀 Основные команды

### Запуск

```bash
# Первый запуск (с сборкой образа)
docker-compose up -d --build

# Обычный запуск
docker-compose up -d
```

### Остановка

```bash
# Остановить контейнеры (данные сохраняются)
docker-compose down

# Остановить + удалить данные БД (ОСТОРОЖНО!)
docker-compose down -v
```

### Перезапуск

```bash
# Перезапустить всё
docker-compose restart

# Только бота
docker-compose restart bot

# Только БД
docker-compose restart postgres
```

### Логи

```bash
# Все логи
docker-compose logs

# Логи бота (live)
docker-compose logs -f bot

# Последние 50 строк логов бота
docker-compose logs --tail=50 bot

# Логи PostgreSQL
docker-compose logs postgres
```

### Статус

```bash
# Статус контейнеров
docker-compose ps

# Использование ресурсов (CPU, RAM)
docker stats

# Детальная информация
docker inspect money_bot
docker inspect money_bot_db
```

---

## 🔧 Продвинутые команды

### Подключение к контейнеру

```bash
# Bash в контейнере бота
docker exec -it money_bot /bin/bash

# Bash в контейнере БД
docker exec -it money_bot_db /bin/bash

# Python REPL в контейнере бота
docker exec -it money_bot python
```

### Работа с БД

```bash
# PostgreSQL CLI
docker exec -it money_bot_db psql -U postgres -d money_bot

# Выполнить SQL запрос
docker exec -it money_bot_db psql -U postgres -d money_bot -c "SELECT COUNT(*) FROM users;"

# Бэкап БД
docker exec money_bot_db pg_dump -U postgres money_bot > backup.sql

# Восстановление БД
cat backup.sql | docker exec -i money_bot_db psql -U postgres -d money_bot
```

### Просмотр файлов в контейнере

```bash
# Файлы в контейнере бота
docker exec money_bot ls -la /app/backend

# Конфиг в контейнере
docker exec money_bot cat /app/backend/config.py

# Логи внутри контейнера
docker exec money_bot cat /app/bot.log
```

---

## 🔄 Обновление кода

После изменения кода нужно пересобрать образ:

```bash
# Пересборка только бота
docker-compose up -d --build bot

# Пересборка всего (редко нужно)
docker-compose up -d --build

# Принудительная пересборка без кэша
docker-compose build --no-cache bot
docker-compose up -d
```

---

## 🧹 Очистка

### Освобождение места

```bash
# Удалить остановленные контейнеры
docker container prune

# Удалить неиспользуемые образы
docker image prune

# Удалить всё неиспользуемое (осторожно!)
docker system prune -a

# Удалить только для этого проекта
docker-compose down --rmi all -v
```

### Сброс к чистому состоянию

```bash
# Полная очистка проекта (УДАЛИТ ДАННЫЕ!)
docker-compose down -v --rmi all
docker-compose up -d --build
```

---

## 🐛 Debugging

### Бот не запускается

```bash
# Проверь логи
docker-compose logs bot

# Проверь что PostgreSQL здоров
docker-compose ps
# postgres должен быть "healthy"

# Проверь переменные окружения
docker exec money_bot env | grep BOT_TOKEN
docker exec money_bot env | grep DB_

# Ручной запуск для отладки
docker-compose run --rm bot python -m backend.bot.main
```

### БД недоступна

```bash
# Проверь что PostgreSQL работает
docker exec money_bot_db pg_isready -U postgres

# Проверь сетевое подключение из контейнера бота
docker exec money_bot ping postgres

# Перезапусти БД
docker-compose restart postgres

# Проверь логи БД
docker-compose logs postgres
```

### Изменения не применяются

```bash
# Docker кэширует старые слои, нужна пересборка
docker-compose build --no-cache bot
docker-compose up -d
```

---

## 📊 Мониторинг

### Использование ресурсов

```bash
# Live статистика
docker stats

# Размер образов
docker images | grep money_bot

# Размер контейнеров
docker ps -s
```

### Логи с ротацией

Уже настроено в `docker-compose.yml`:
```yaml
logging:
  driver: "json-file"
  options:
    max-size: "10m"   # Максимум 10 МБ на файл
    max-file: "3"     # Хранить 3 файла (всего 30 МБ)
```

---

## 🔐 Безопасность

### Хорошие практики

1. **Не коммить `.env`** (уже в `.gitignore`)
2. **Сильные пароли БД** в `.env`:
   ```env
   DB_PASSWORD=Strong_P@ssw0rd_123!
   ```
3. **Закрыть порт PostgreSQL** (убрать `ports:` из docker-compose.yml)
4. **Регулярно обновлять образы**:
   ```bash
   docker-compose pull
   docker-compose up -d --build
   ```

---

## 🌐 Сети Docker

Бот и БД общаются через внутреннюю сеть `money_bot_network`.

```bash
# Информация о сети
docker network inspect money_bot_network

# Контейнеры в сети
docker network inspect money_bot_network | grep Name
```

Бот подключается к PostgreSQL по имени сервиса: `postgres` (не `localhost`!)

---

## 💾 Volumes (данные)

Данные PostgreSQL хранятся в Docker volume `postgres_data`.

```bash
# Список volumes
docker volume ls

# Информация о volume
docker volume inspect money_bot_postgres_data

# Размер данных
docker system df -v | grep postgres_data

# Бэкап volume (продвинуто)
docker run --rm -v money_bot_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz /data
```

---

## 🚀 Производительность

### Оптимизация сборки

Уже применено:
- Multi-stage не нужен (образ и так легкий)
- Зависимости копируются первыми (кэширование слоев)
- `--no-cache-dir` для pip (меньше размер)
- `.dockerignore` исключает лишнее

### Оптимизация runtime

```yaml
# В docker-compose.yml можно добавить лимиты:
services:
  bot:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

---

## 📚 Полезные ссылки

- [Docker Compose CLI](https://docs.docker.com/compose/reference/)
- [Dockerfile best practices](https://docs.docker.com/develop/develop-images/dockerfile_best-practices/)
- [Docker logs](https://docs.docker.com/engine/reference/commandline/logs/)

---

## ✅ Чек-лист Docker setup

- [x] Dockerfile создан (Python 3.13-slim)
- [x] docker-compose.yml настроен (бот + PostgreSQL)
- [x] .dockerignore создан
- [x] Health checks настроены
- [x] Логи с ротацией
- [x] Автоперезапуск (restart: unless-stopped)
- [x] Сетевая изоляция
- [x] Volume для данных БД
- [x] Graceful shutdown

---

**Готово!** Теперь ты знаешь всё про Docker для Money Bot 🐳





