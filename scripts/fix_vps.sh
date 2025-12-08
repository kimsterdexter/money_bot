#!/bin/bash

# Скрипт исправления VPS для Money Bot
# Выполнять на VPS под пользователем kimster

set -e

echo "🔧 Исправление настроек VPS..."
echo ""

# 1. Обновляем Docker
echo "🐳 Обновление Docker..."
sudo apt-get remove docker.io docker-compose -y 2>/dev/null || true
curl -fsSL https://get.docker.com | sudo sh
sudo systemctl enable docker
sudo systemctl start docker

# 2. Устанавливаем новый Docker Compose
echo "🐳 Установка Docker Compose..."
sudo curl -SL https://github.com/docker/compose/releases/latest/download/docker-compose-linux-x86_64 -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
sudo ln -sf /usr/local/bin/docker-compose /usr/bin/docker-compose

# 3. Добавляем пользователей в группу docker
echo "👥 Настройка прав Docker..."
sudo usermod -aG docker kimster
sudo usermod -aG docker gitlab-runner 2>/dev/null || echo "gitlab-runner будет добавлен позже"

# 4. Исправляем структуру проекта
echo "📁 Исправление структуры проекта..."
cd /opt/money_bot
if [ -d "money_bot" ]; then
    sudo mv money_bot/* . 2>/dev/null || true
    sudo mv money_bot/.* . 2>/dev/null || true
    sudo rmdir money_bot 2>/dev/null || true
fi

# 5. Настраиваем права на директорию
echo "🔐 Настройка прав..."
sudo chown -R kimster:kimster /opt/money_bot

# 6. Настраиваем sudoers
echo "⚙️ Настройка sudoers..."
echo 'kimster ALL=(ALL) NOPASSWD: /usr/bin/docker, /usr/local/bin/docker-compose, /usr/bin/docker-compose' | sudo tee /etc/sudoers.d/kimster
sudo chmod 0440 /etc/sudoers.d/kimster

# 7. Перезагружаем Docker
echo "🔄 Перезапуск Docker..."
sudo systemctl restart docker

# 8. Перезапускаем GitLab Runner
echo "🏃 Перезапуск GitLab Runner..."
sudo gitlab-runner restart 2>/dev/null || echo "Runner будет запущен после регистрации"

echo ""
echo "✅ Исправления применены!"
echo ""
echo "📋 ВАЖНО: Сделай logout и login заново для применения группы docker:"
echo "   exit"
echo "   ssh kimster@94.241.141.105"
echo ""
echo "После перелогина проверь:"
echo "   docker ps"
echo "   docker-compose --version"
echo "   cd /opt/money_bot && ls -la"
echo ""





