# 🚀 Deploy через GitLab CI/CD

Полная инструкция по настройке автоматического деплоя на VPS через GitLab Runner.

---

## 📋 Что нужно:

- ✅ VPS (Ubuntu 20.04+/Debian 11+)
- ✅ SSH доступ к VPS (root или sudo)
- ✅ GitLab репозиторий
- ✅ Домен (опционально)

---

## 🎯 Шаг 1: Подготовка VPS

### 1.1 Подключись к VPS

```bash
ssh root@your-server-ip
```

### 1.2 Запусти скрипт настройки сервера

```bash
# Скопируй скрипт на сервер
curl -o setup_server.sh https://raw.githubusercontent.com/your-repo/money_bot/main/scripts/setup_server.sh

# Или загрузи вручную и выполни:
chmod +x setup_server.sh
./setup_server.sh
```

**Скрипт установит:**
- Docker и Docker Compose
- Git
- Firewall (UFW)
- Fail2ban
- Создаст пользователя deployer

### 1.3 Настрой SSH для deployer

```bash
# Переключись на пользователя deployer
su - deployer

# Создай SSH ключ
ssh-keygen -t ed25519 -C "deployer@money-bot"

# Добавь публичный ключ в authorized_keys
cat ~/.ssh/id_ed25519.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys

# Скопируй ПРИВАТНЫЙ ключ (понадобится для GitLab)
cat ~/.ssh/id_ed25519
# Скопируй весь вывод включая -----BEGIN и -----END
```

### 1.4 Склонируй репозиторий

```bash
# Под пользователем deployer
cd /opt
git clone https://gitlab.com/your-username/money_bot.git
cd money_bot
```

---

## 🏃 Шаг 2: Установка GitLab Runner

### 2.1 Запусти скрипт установки runner

```bash
# От root
exit  # Выйди из deployer
curl -o install_runner.sh https://raw.githubusercontent.com/your-repo/money_bot/main/scripts/install_runner.sh
chmod +x install_runner.sh
./install_runner.sh
```

### 2.2 Получи Registration Token

1. Открой GitLab → твой проект
2. Settings → CI/CD
3. Runners → Expand
4. Скопируй **Registration token**

### 2.3 Зарегистрируй Runner

```bash
sudo gitlab-runner register
```

**Параметры:**
```
GitLab instance URL: https://gitlab.com/
Registration token: [вставь свой token]
Description: money-bot-production
Tags: shell
Executor: shell
```

### 2.4 Настрой права

```bash
# Добавь gitlab-runner в группу docker
sudo usermod -aG docker gitlab-runner

# Перезапусти runner
sudo gitlab-runner restart

# Проверь статус
sudo gitlab-runner status
```

---

## 🔐 Шаг 3: Настройка переменных в GitLab

### 3.1 Открой GitLab

GitLab → твой проект → Settings → CI/CD → Variables → Expand

### 3.2 Добавь переменные (нажми "Add variable" для каждой):

#### **SSH доступ:**

| Key | Value | Protected | Masked |
|-----|-------|-----------|--------|
| `SSH_PRIVATE_KEY` | [приватный ключ deployer из шага 1.3] | ✅ | ✅ |
| `SERVER_IP` | IP твоего VPS (например: 185.123.45.67) | ✅ | ❌ |
| `SERVER_USER` | `kimster` | ✅ | ❌ |

#### **Telegram Bot:**

| Key | Value | Protected | Masked |
|-----|-------|-----------|--------|
| `BOT_TOKEN` | [твой токен от BotFather] | ✅ | ✅ |

#### **База данных:**

| Key | Value | Protected | Masked |
|-----|-------|-----------|--------|
| `DB_NAME` | `money_bot` | ✅ | ❌ |
| `DB_USER` | `postgres` | ✅ | ❌ |
| `DB_PASSWORD` | [сильный пароль!] | ✅ | ✅ |

#### **Настройки бота:**

| Key | Value | Protected | Masked |
|-----|-------|-----------|--------|
| `DAILY_INCOME_TIME` | `09:00` | ❌ | ❌ |
| `DAILY_EXPENSE_TIME` | `20:00` | ❌ | ❌ |
| `TIMEZONE` | `Europe/Moscow` | ❌ | ❌ |

**Важно:**
- ✅ **Protected** = переменная доступна только в protected branches (main)
- ✅ **Masked** = значение будет замаскировано в логах

---

## 🚀 Шаг 4: Первый деплой

### 4.1 Закоммить и запушить изменения

```bash
# На локальной машине
cd /Users/kimster/Projects/money_bot

git add .
git commit -m "Add GitLab CI/CD configuration"
git push origin main
```

### 4.2 Открой GitLab Pipeline

GitLab → твой проект → CI/CD → Pipelines

Увидишь новый pipeline с двумя стейджами:
- ⚙️ **test** (автоматически)
- 🚀 **deploy_production** (вручную)

### 4.3 Запусти деплой

1. Нажми на pipeline
2. Найди стейдж **deploy_production**
3. Нажми ▶️ кнопку "Play"
4. Наблюдай логи деплоя

### 4.4 Проверь результат

После завершения pipeline:

```bash
# Подключись к VPS
ssh deployer@your-server-ip

# Проверь статус
cd /opt/money_bot
docker-compose ps

# Посмотри логи
docker-compose logs -f bot
```

---

## ✅ Готово! Бот задеплоен

Теперь при каждом пуше в `main` будет автоматически:
1. ✅ Запускаться тесты
2. ⏸️ Ждать ручного подтверждения деплоя
3. 🚀 Деплоиться на продакшен при нажатии "Play"

---

## 🔄 Как деплоить обновления

### Автоматический деплой (рекомендуется):

```bash
# 1. Внеси изменения в код
# 2. Закоммить
git add .
git commit -m "Добавил новую фичу"
git push origin main

# 3. Открой GitLab → Pipelines
# 4. Нажми Play на deploy_production
# 5. Готово!
```

### Ручной деплой (если нужно):

```bash
ssh deployer@your-server-ip
cd /opt/money_bot
git pull origin main
docker-compose down
docker-compose up -d --build
```

---

## 📊 Мониторинг на продакшене

### Логи

```bash
# Логи бота (live)
docker-compose logs -f bot

# Логи БД
docker-compose logs -f postgres

# Последние 100 строк
docker-compose logs --tail=100 bot
```

### Статус

```bash
# Статус контейнеров
docker-compose ps

# Использование ресурсов
docker stats
```

### Перезапуск

```bash
# Перезапуск бота
docker-compose restart bot

# Перезапуск всего
docker-compose restart

# Полная пересборка
docker-compose down
docker-compose up -d --build
```

---

## 🔒 Безопасность

### ✅ Что уже настроено:

- Firewall (UFW) - открыты только SSH (22), HTTP (80), HTTPS (443)
- Fail2ban - защита от брутфорса SSH
- Docker network isolation - БД недоступна снаружи
- Переменные окружения замаскированы в GitLab

### 🔐 Дополнительно (рекомендуется):

1. **Смени SSH порт:**
```bash
sudo nano /etc/ssh/sshd_config
# Измени Port 22 на Port 2222
sudo systemctl restart sshd
```

2. **Отключи root SSH:**
```bash
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no
sudo systemctl restart sshd
```

3. **Настрой автоматические обновления:**
```bash
sudo apt-get install unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

4. **Настрой резервное копирование БД** (см. PRODUCTION.md)

---

## 🐛 Troubleshooting

### Pipeline падает на deploy

**Проблема:** `Permission denied (publickey)`

**Решение:**
1. Проверь что `SSH_PRIVATE_KEY` в GitLab переменных правильный
2. Проверь что публичный ключ добавлен в `~/.ssh/authorized_keys` на сервере
3. Проверь права: `chmod 600 ~/.ssh/authorized_keys`

---

### Бот не запускается на сервере

**Проблема:** `TokenValidationError` или другие ошибки

**Решение:**
```bash
# Проверь переменные окружения
docker exec money_bot env | grep BOT_TOKEN

# Проверь логи
docker-compose logs bot

# Пересоздай контейнеры
docker-compose down
docker-compose up -d --build
```

---

### Runner не подключается

**Проблема:** Runner offline в GitLab

**Решение:**
```bash
# Проверь статус
sudo gitlab-runner status

# Перезапусти
sudo gitlab-runner restart

# Проверь логи
sudo journalctl -u gitlab-runner -f
```

---

## 📚 Полезные ссылки

- [GitLab CI/CD Documentation](https://docs.gitlab.com/ee/ci/)
- [GitLab Runner Installation](https://docs.gitlab.com/runner/install/)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
- [PRODUCTION.md](./PRODUCTION.md) - Production deploy guide

---

## 🎯 Структура CI/CD

```
Push to main
    ↓
Test stage (автоматически)
    ├── Установка зависимостей
    ├── Запуск тестов
    └── ✅ Успех / ❌ Провал
    ↓
Deploy stage (вручную - нажать Play)
    ├── SSH подключение к VPS
    ├── Git pull
    ├── Создание .env
    ├── Docker Compose down
    ├── Docker Compose up --build
    ├── Проверка статуса
    └── ✅ Деплой завершен
```

---

**Готово!** Полностью автоматизированный деплой настроен 🚀

