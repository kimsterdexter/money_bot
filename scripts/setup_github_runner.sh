#!/bin/bash

# Скрипт установки GitHub Actions Runner на VPS
# Выполнять на VPS под пользователем kimster

set -e

echo "🏃 Установка GitHub Actions Runner..."
echo ""

# Директория для runner
RUNNER_DIR="/home/kimster/actions-runner"

# Создаем директорию
mkdir -p $RUNNER_DIR
cd $RUNNER_DIR

# Качаем последнюю версию runner
echo "📦 Загрузка GitHub Actions Runner..."
RUNNER_VERSION=$(curl -s https://api.github.com/repos/actions/runner/releases/latest | grep 'tag_name' | cut -d '"' -f 4 | sed 's/v//')
curl -o actions-runner-linux-x64.tar.gz -L https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-x64-${RUNNER_VERSION}.tar.gz

# Распаковываем
echo "📦 Распаковка..."
tar xzf ./actions-runner-linux-x64.tar.gz
rm actions-runner-linux-x64.tar.gz

echo ""
echo "✅ Runner загружен!"
echo ""
echo "📋 Следующие шаги:"
echo ""
echo "1. Получи registration token:"
echo "   GitHub → Settings → Actions → Runners → New self-hosted runner"
echo ""
echo "2. Настрой runner (из директории $RUNNER_DIR):"
echo "   cd $RUNNER_DIR"
echo "   ./config.sh --url https://github.com/kimsterdexter/money_bot --token YOUR_TOKEN"
echo ""
echo "3. Установи как сервис:"
echo "   sudo ./svc.sh install kimster"
echo "   sudo ./svc.sh start"
echo ""
echo "4. Проверь статус:"
echo "   sudo ./svc.sh status"
echo ""





