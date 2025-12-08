#!/bin/bash

# Скрипт установки GitLab Runner на Ubuntu/Debian
# Запускать от root или с sudo

set -e

echo "🏃 Установка GitLab Runner..."
echo ""

# Добавление официального репозитория GitLab
echo "📦 Добавление репозитория GitLab..."
curl -L "https://packages.gitlab.com/install/repositories/runner/gitlab-runner/script.deb.sh" | bash

# Установка GitLab Runner
echo "📦 Установка GitLab Runner..."
apt-get install gitlab-runner -y

# Проверка установки
echo ""
echo "✅ GitLab Runner установлен!"
gitlab-runner --version

echo ""
echo "📋 Следующие шаги:"
echo ""
echo "1. Получи registration token:"
echo "   GitLab → Settings → CI/CD → Runners → Expand"
echo ""
echo "2. Зарегистрируй runner:"
echo "   sudo gitlab-runner register"
echo ""
echo "   GitLab URL: https://gitlab.com/"
echo "   Token: [твой token]"
echo "   Description: money-bot-production"
echo "   Tags: shell"
echo "   Executor: shell"
echo ""
echo "3. Добавь gitlab-runner в группу docker:"
echo "   sudo usermod -aG docker gitlab-runner"
echo ""
echo "4. Перезапусти runner:"
echo "   sudo gitlab-runner restart"
echo ""





