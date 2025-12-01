#!/bin/bash

# Скрипт для первоначальной настройки сервера
# Запускать от root или с sudo

set -e

echo "🚀 Настройка сервера для Money Bot..."
echo ""

# Обновление системы
echo "📦 Обновление системы..."
apt-get update
apt-get upgrade -y

# Установка необходимых пакетов
echo "📦 Установка зависимостей..."
apt-get install -y \
    curl \
    git \
    ufw \
    fail2ban

# Установка Docker
if ! command -v docker &> /dev/null; then
    echo "🐳 Установка Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    rm get-docker.sh
    systemctl enable docker
    systemctl start docker
else
    echo "✅ Docker уже установлен"
fi

# Установка Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "🐳 Установка Docker Compose..."
    apt-get install -y docker-compose
else
    echo "✅ Docker Compose уже установлен"
fi

# Создание пользователя для деплоя (если не существует)
if ! id -u deployer &>/dev/null; then
    echo "👤 Создание пользователя deployer..."
    useradd -m -s /bin/bash deployer
    usermod -aG docker deployer
    echo "deployer ALL=(ALL) NOPASSWD: /usr/bin/docker-compose" >> /etc/sudoers.d/deployer
else
    echo "✅ Пользователь deployer уже существует"
fi

# Создание директории для приложения
echo "📁 Создание директории приложения..."
mkdir -p /opt/money_bot
chown deployer:deployer /opt/money_bot

# Настройка firewall
echo "🔥 Настройка firewall..."
ufw --force enable
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw reload

# Настройка fail2ban
echo "🔒 Настройка fail2ban..."
systemctl enable fail2ban
systemctl start fail2ban

echo ""
echo "✅ Сервер настроен!"
echo ""
echo "📋 Следующие шаги:"
echo "1. Создай SSH ключ для deployer: ssh-keygen (под пользователем deployer)"
echo "2. Добавь публичный ключ в ~/.ssh/authorized_keys"
echo "3. Склонируй репозиторий в /opt/money_bot"
echo "4. Установи GitLab Runner"
echo ""

