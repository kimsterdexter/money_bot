# 🛡️ Руководство по безопасности Money Bot

Полное руководство по защите VPS и приложения от атак.

---

## 🎯 Уровни защиты

### 1️⃣ Сетевая защита
### 2️⃣ Защита SSH
### 3️⃣ Защита приложения
### 4️⃣ Защита данных
### 5️⃣ Мониторинг и алерты

---

## 🚀 Быстрая настройка (один скрипт)

```bash
# На VPS под sudo
cd /opt/money_bot
curl -O https://raw.githubusercontent.com/kimsterdexter/money_bot/main/scripts/security_hardening.sh
chmod +x security_hardening.sh
sudo ./security_hardening.sh
```

---

## 1️⃣ Сетевая защита

### UFW (Uncomplicated Firewall)

```bash
# Установка
sudo apt-get install -y ufw

# Настройка
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Разрешаем только нужные порты
sudo ufw allow 22/tcp    # SSH
sudo ufw limit 22/tcp    # Защита от флуда SSH

# НЕ открывай PostgreSQL наружу!
# sudo ufw allow 5432/tcp  # ❌ НИКОГДА!

# Активация
sudo ufw --force enable

# Проверка
sudo ufw status verbose
```

### Проверка открытых портов

```bash
# Какие порты слушают
sudo ss -tulpn | grep LISTEN

# Должно быть только:
# - 22 (SSH)
# Больше ничего наружу!

# PostgreSQL должен быть только 127.0.0.1:5432 или в Docker сети
```

---

## 2️⃣ Защита SSH

### A. SSH ключи (обязательно!)

```bash
# На локальной машине (Mac)
ssh-keygen -t ed25519 -C "your_email@example.com"

# Копируй публичный ключ на VPS
ssh-copy-id kimster@94.241.141.105

# Проверь что работает
ssh kimster@94.241.141.105
```

### B. Отключение пароля и root

```bash
# На VPS под sudo
sudo nano /etc/ssh/sshd_config

# Измени:
PermitRootLogin no                # Запретить root
PasswordAuthentication no         # Только SSH ключи
PubkeyAuthentication yes          # Разрешить ключи
MaxAuthTries 3                    # Максимум 3 попытки

# Применить
sudo systemctl restart sshd
```

### C. Смена SSH порта (опционально)

```bash
# В /etc/ssh/sshd_config
Port 2222  # Вместо 22

# Не забудь обновить firewall!
sudo ufw allow 2222/tcp
sudo ufw delete allow 22/tcp

# Перезапусти
sudo systemctl restart sshd

# Подключение теперь:
ssh -p 2222 kimster@94.241.141.105
```

### D. Fail2ban (защита от брутфорса)

```bash
# Установка
sudo apt-get install -y fail2ban

# Конфигурация
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600       # Бан на 1 час
findtime = 600       # Окно 10 минут
maxretry = 3         # Максимум 3 попытки

[sshd]
enabled = true
port = 22
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
```

```bash
# Запуск
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Проверка
sudo fail2ban-client status sshd
```

---

## 3️⃣ Защита приложения

### A. Docker security

#### 1. Закрыть порты PostgreSQL

В `docker-compose.yml`:

```yaml
postgres:
  # ❌ НЕ публикуй порты наружу!
  # ports:
  #   - "5432:5432"
  
  # ✅ Только внутри Docker сети
  networks:
    - money_bot_network
```

#### 2. Сильные пароли

```env
# ❌ Плохо
DB_PASSWORD=postgres

# ✅ Хорошо (минимум 16 символов)
DB_PASSWORD=SecurePassword123Strong
```

#### 3. Ограничение ресурсов

```yaml
services:
  bot:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

#### 4. Read-only filesystem (опционально)

```yaml
bot:
  read_only: true
  tmpfs:
    - /tmp
```

### B. Secrets management

**Все секреты только в GitHub Secrets, НЕ в коде!**

```bash
# ❌ Плохо - в коде
BOT_TOKEN=123456789:ABC...

# ✅ Хорошо - в GitHub Secrets
${{ secrets.BOT_TOKEN }}
```

---

## 4️⃣ Защита данных

### A. Автоматические бэкапы

```bash
# Настройка
cd /opt/money_bot
curl -O https://raw.githubusercontent.com/kimsterdexter/money_bot/main/scripts/setup_backups.sh
chmod +x setup_backups.sh
./setup_backups.sh
```

Скрипт настроит:
- ✅ Ежедневные бэкапы в 3:00
- ✅ Ротацию (хранит 30 дней)
- ✅ Сжатие gzip
- ✅ Логирование

### B. Ручной бэкап

```bash
# Бэкап
docker exec money_bot_db pg_dump -U postgres money_bot | gzip > backup_$(date +%Y%m%d).sql.gz

# Восстановление
gunzip -c backup_20251208.sql.gz | docker exec -i money_bot_db psql -U postgres -d money_bot
```

### C. Проверка бэкапов

```bash
# Список бэкапов
ls -lh ~/backups/

# Тестовое восстановление (в тестовую БД)
docker exec money_bot_db psql -U postgres -c "CREATE DATABASE money_bot_test;"
gunzip -c backup.sql.gz | docker exec -i money_bot_db psql -U postgres -d money_bot_test
```

---

## 5️⃣ Мониторинг и алерты

### A. Проверка статуса системы

```bash
# Использование диска
df -h

# Память
free -h

# CPU и процессы
htop

# Docker статистика
docker stats

# Логи системы
sudo journalctl -xe
```

### B. Мониторинг логов

```bash
# Логи бота (live)
docker-compose logs -f bot

# Последние ошибки
docker-compose logs bot | grep ERROR

# Логи SSH попыток входа
sudo tail -f /var/log/auth.log

# Fail2ban статус
sudo fail2ban-client status sshd
```

### C. Алерты через Telegram (опционально)

Создай скрипт мониторинга:

```bash
#!/bin/bash
# ~/monitor.sh

BOT_TOKEN="your_bot_token"
CHAT_ID="your_chat_id"

# Проверка места на диске
DISK_USAGE=$(df / | tail -1 | awk '{print $5}' | sed 's/%//')
if [ $DISK_USAGE -gt 80 ]; then
    curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
        -d chat_id=$CHAT_ID \
        -d text="⚠️ Disk usage: ${DISK_USAGE}%"
fi

# Проверка что бот работает
if ! docker-compose ps | grep -q "Up (healthy)"; then
    curl -s -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
        -d chat_id=$CHAT_ID \
        -d text="❌ Bot is down!"
fi
```

Добавь в crontab:
```bash
*/15 * * * * /home/kimster/monitor.sh
```

---

## 6️⃣ Автоматические обновления безопасности

```bash
# Установка
sudo apt-get install -y unattended-upgrades apt-listchanges

# Настройка
sudo dpkg-reconfigure -plow unattended-upgrades

# Конфигурация
sudo nano /etc/apt/apt.conf.d/50unattended-upgrades
```

```
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};
Unattended-Upgrade::Automatic-Reboot "false";
```

---

## 7️⃣ Дополнительные меры

### A. Отключить ненужные сервисы

```bash
# Список сервисов
systemctl list-unit-files --state=enabled

# Отключить ненужные (пример)
sudo systemctl disable bluetooth.service
```

### B. Минимизация прав

```bash
# Бот работает от непривилегированного пользователя
# Никакого sudo в контейнере
# Docker socket не пробрасывать
```

### C. Регулярные аудиты

```bash
# Проверка открытых портов
sudo ss -tulpn

# Проверка процессов
ps aux | grep -E 'postgres|python'

# Проверка Docker контейнеров
docker ps -a

# Проверка volumes
docker volume ls
```

---

## ✅ Чек-лист безопасности

### Базовая безопасность:
- [ ] UFW firewall активирован
- [ ] Только SSH порт открыт (22)
- [ ] SSH ключи настроены
- [ ] Пароли отключены для SSH
- [ ] Root login отключен
- [ ] Fail2ban установлен и работает
- [ ] Сильный пароль БД (16+ символов)
- [ ] PostgreSQL порт закрыт наружу

### Защита приложения:
- [ ] Все секреты в GitHub Secrets
- [ ] .env в .gitignore
- [ ] Docker логи с ротацией
- [ ] Ресурсы контейнеров ограничены

### Защита данных:
- [ ] Автоматические бэкапы настроены
- [ ] Бэкапы тестируются раз в месяц
- [ ] Ротация бэкапов (30 дней)

### Мониторинг:
- [ ] Логи регулярно проверяются
- [ ] Алерты настроены (опционально)
- [ ] Автообновления безопасности включены

---

## 🚨 Что делать при взломе

### 1. Немедленная изоляция

```bash
# Отключи сеть
sudo ufw deny out
sudo docker-compose down
```

### 2. Анализ

```bash
# Проверь логи
sudo tail -1000 /var/log/auth.log
docker-compose logs --since 24h

# Проверь процессы
ps aux
docker ps -a

# Проверь изменения файлов
sudo find /opt/money_bot -mtime -7 -ls
```

### 3. Восстановление

```bash
# Из бэкапа
gunzip -c backup.sql.gz | docker exec -i money_bot_db psql -U postgres -d money_bot

# Пересоздай контейнеры
docker-compose down -v
docker-compose up -d --build
```

### 4. Усиление

```bash
# Смени все пароли
# Обнови SSH ключи
# Проверь firewall правила
# Обнови систему
```

---

## 📚 Полезные ссылки

- [Docker Security](https://docs.docker.com/engine/security/)
- [Ubuntu Server Security](https://ubuntu.com/server/docs/security-introduction)
- [PostgreSQL Security](https://www.postgresql.org/docs/current/security.html)
- [Fail2ban Manual](https://www.fail2ban.org/wiki/index.php/Manual)

---

**Помни: безопасность - это процесс, а не состояние!** 🛡️

Регулярно проверяй и обновляй защиту.

