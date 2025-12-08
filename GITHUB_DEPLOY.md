# 🚀 Deploy через GitHub Actions с Self-Hosted Runner

Инструкция по настройке автоматического деплоя через GitHub Actions с собственным runner на VPS.

---

## 🎯 Преимущества Self-Hosted Runner:

- ✅ **Бесплатно** (не тратятся минуты GitHub)
- ✅ **Быстрее** (деплой прямо на сервере, без SSH)
- ✅ **Приватный доступ** к Docker и файлам
- ✅ **Нет лимитов** на время выполнения

---

## 🏃 Шаг 1: Установка GitHub Runner на VPS

### На VPS (SSH сессия):

```bash
# 1. Скачай и запусти скрипт установки
cd /opt/money_bot
curl -O https://raw.githubusercontent.com/kimsterdexter/money_bot/main/scripts/setup_github_runner.sh
chmod +x setup_github_runner.sh
./setup_github_runner.sh
```

Или вручную:

```bash
# Создай директорию для runner
mkdir -p ~/actions-runner && cd ~/actions-runner

# Скачай последнюю версию
curl -o actions-runner-linux-x64.tar.gz -L \
  https://github.com/actions/runner/releases/download/v2.321.0/actions-runner-linux-x64-2.321.0.tar.gz

# Распакуй
tar xzf ./actions-runner-linux-x64.tar.gz
rm actions-runner-linux-x64.tar.gz
```

---

## 🔑 Шаг 2: Регистрация Runner в GitHub

### 2.1 Получи Registration Token

1. Открой **GitHub** → твой репозиторий `kimsterdexter/money_bot`
2. **Settings** → **Actions** → **Runners**
3. Нажми **New self-hosted runner**
4. Выбери **Linux** → **x64**
5. Скопируй **token** из команды (выглядит как `AXXXXXXXXXXXXXXXXXXXXXXXX`)

### 2.2 Настрой Runner

```bash
cd ~/actions-runner

# Запусти конфигурацию (подставь свой token!)
./config.sh \
  --url https://github.com/kimsterdexter/money_bot \
  --token YOUR_TOKEN_HERE

# Ответы на вопросы:
# Runner group: (Enter - default)
# Runner name: money-bot-production
# Labels: (Enter - default: self-hosted,Linux,X64)
# Work folder: (Enter - default: _work)
```

### 2.3 Установи как системный сервис

```bash
# Установка сервиса
sudo ./svc.sh install kimster

# Запуск
sudo ./svc.sh start

# Проверка статуса
sudo ./svc.sh status
```

### 2.4 Проверь в GitHub

Открой **GitHub → Settings → Actions → Runners**

Должен появиться runner со статусом **🟢 Idle**

---

## 🔐 Шаг 3: Настройка Secrets в GitHub

### 3.1 Открой GitHub

**GitHub** → твой репозиторий → **Settings** → **Secrets and variables** → **Actions**

### 3.2 Добавь secrets (нажми "New repository secret"):

| Name | Value | Описание |
|------|-------|----------|
| `BOT_TOKEN` | `7624606204:AAH5pUk2gwiSQyL_UD-ggElydtpzMsBCpbU` | Токен бота |
| `DB_NAME` | `money_bot` | Имя БД |
| `DB_USER` | `postgres` | Пользователь БД |
| `DB_PASSWORD` | `[придумай сильный пароль]` | Пароль БД |
| `DAILY_INCOME_TIME` | `09:00` | Время напоминания о доходах |
| `DAILY_EXPENSE_TIME` | `20:00` | Время напоминания о расходах |
| `TIMEZONE` | `Europe/Moscow` | Часовой пояс |

**Важно:** Secrets автоматически маскируются в логах!

---

## 🚀 Шаг 4: Настройка рабочей директории

Runner будет клонировать код в `~/actions-runner/_work/money_bot/money_bot`, но деплоить нужно в `/opt/money_bot`.

### Создай симлинк:

```bash
# На VPS
cd /opt/money_bot

# Когда runner запустится первый раз, он создаст директорию _work
# После первого запуска workflow выполни:
sudo ln -sf ~/actions-runner/_work/money_bot/money_bot /opt/money_bot/code
```

### Или настрой runner работать прямо в /opt/money_bot:

```bash
# Останови runner
sudo ~/actions-runner/svc.sh stop

# Удали конфигурацию
cd ~/actions-runner
./config.sh remove

# Переконфигурируй с новой work-folder
./config.sh \
  --url https://github.com/kimsterdexter/money_bot \
  --token YOUR_NEW_TOKEN \
  --work /opt/money_bot

# Перезапусти
sudo ./svc.sh install kimster
sudo ./svc.sh start
```

---

## 🎯 Шаг 5: Первый деплой!

### 5.1 Закоммить изменения

```bash
# На локальной машине
cd /Users/kimster/Projects/money_bot

git add .
git commit -m "Add GitHub Actions with self-hosted runner"
git push origin main
```

### 5.2 Проверь workflow

1. Открой **GitHub** → **Actions**
2. Увидишь workflow **"Deploy to Production"**
3. Кликни на него, чтобы увидеть логи
4. Должен пройти через stages: **test** → **deploy**

### 5.3 Проверь на VPS

```bash
ssh kimster@94.241.141.105
cd /opt/money_bot

# Статус контейнеров
docker-compose ps

# Логи бота
docker-compose logs -f bot
```

**Готово!** 🎉 Бот задеплоен через GitHub Actions!

---

## 🔄 Как деплоить обновления

### Автоматически при каждом push:

```bash
git add .
git commit -m "Update feature"
git push origin main
```

→ GitHub автоматически запустит workflow  
→ Тесты пройдут  
→ Деплой выполнится  
→ Бот обновится

### Ручной запуск:

1. **GitHub** → **Actions**
2. Выбери **Deploy to Production**
3. **Run workflow** → **Run workflow**

---

## 📊 Мониторинг

### Логи workflow:
**GitHub** → **Actions** → выбери запуск → смотри логи каждого step

### Логи бота на VPS:
```bash
docker-compose logs -f bot
```

### Статус runner:
```bash
# На VPS
sudo ~/actions-runner/svc.sh status

# Или в GitHub
# Settings → Actions → Runners
```

---

## 🛠 Управление Runner

### Перезапуск:
```bash
sudo ~/actions-runner/svc.sh restart
```

### Остановка:
```bash
sudo ~/actions-runner/svc.sh stop
```

### Удаление:
```bash
sudo ~/actions-runner/svc.sh stop
sudo ~/actions-runner/svc.sh uninstall
cd ~/actions-runner
./config.sh remove
```

### Логи runner:
```bash
sudo journalctl -u actions.runner.kimsterdexter-money_bot.money-bot-production -f
```

---

## 🐛 Troubleshooting

### Runner offline в GitHub

**Проблема:** Runner показывает 🔴 Offline

**Решение:**
```bash
# Проверь статус сервиса
sudo ~/actions-runner/svc.sh status

# Перезапусти
sudo ~/actions-runner/svc.sh restart

# Проверь логи
sudo journalctl -u actions.runner.* -f
```

---

### Workflow падает с ошибкой

**Проблема:** Error: "docker-compose: command not found"

**Решение:**
```bash
# Убедись что kimster в группе docker
sudo usermod -aG docker kimster

# Проверь docker-compose
which docker-compose
docker-compose --version

# Перезапусти runner
sudo ~/actions-runner/svc.sh restart
```

---

### Secrets не применяются

**Проблема:** Бот не запускается из-за неправильного токена

**Решение:**
1. Проверь что secrets добавлены в **Settings → Secrets**
2. Имена должны совпадать точно (case-sensitive)
3. Перезапусти workflow

---

## 🔒 Безопасность

### ✅ Что настроено:

- Runner работает от непривилегированного пользователя `kimster`
- Secrets маскируются в логах
- Docker изолирован в сети
- Runner автоматически обновляется

### 🔐 Дополнительно (опционально):

1. **Ограничь доступ к runner только для main:**
   - GitHub → Settings → Actions → Runner groups → Edit
   - Выбери "Selected workflows" → укажи `deploy.yml`

2. **Включи required approvals:**
   - Settings → Environments → production → Add protection rule
   - Require reviewers → добавь себя

---

## 📚 Полезные ссылки

- [GitHub Actions Self-Hosted Runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Docker in GitHub Actions](https://docs.docker.com/ci-cd/github-actions/)

---

## 🎯 Структура CI/CD

```
Push to main
    ↓
GitHub Actions запускается
    ↓
Self-hosted runner на VPS получает задачу
    ↓
Test job (на VPS)
    ├── Checkout code
    └── Run tests
    ↓
Deploy job (на VPS)
    ├── Checkout code
    ├── Create .env from secrets
    ├── docker-compose down
    ├── docker-compose up --build
    └── Check status
    ↓
✅ Бот обновлен и работает!
```

---

**Готово!** Self-hosted runner настроен и работает 🚀





