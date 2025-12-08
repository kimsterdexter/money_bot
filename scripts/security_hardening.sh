#!/bin/bash

# Скрипт полной защиты VPS для Money Bot
# Выполнять от sudo на VPS

set -e

echo "🛡️ Усиленная защита VPS..."
echo ""

# 1. Обновление системы
echo "📦 Обновление системы..."
apt-get update
apt-get upgrade -y

# 2. Настройка UFW (Firewall)
echo "🔥 Настройка firewall..."
apt-get install -y ufw

# Блокируем всё по умолчанию
ufw default deny incoming
ufw default allow outgoing

# Разрешаем только SSH (22)
ufw allow 22/tcp
ufw allow 80/tcp   # HTTP (если нужен)
ufw allow 443/tcp  # HTTPS (если нужен)

# Включаем защиту от флуда
ufw limit 22/tcp

# Активируем
ufw --force enable

echo "✅ Firewall настроен"

# 3. Fail2ban - защита от брутфорса
echo "🔒 Установка Fail2ban..."
apt-get install -y fail2ban

# Конфиг для SSH
cat > /etc/fail2ban/jail.local << 'EOF'
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3
destemail = root@localhost
sendername = Fail2Ban

[sshd]
enabled = true
port = 22
logpath = /var/log/auth.log
maxretry = 3
bantime = 3600
EOF

systemctl enable fail2ban
systemctl restart fail2ban

echo "✅ Fail2ban настроен"

# 4. Отключаем root login через SSH
echo "🔐 Защита SSH..."
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sed -i 's/^#*PubkeyAuthentication.*/PubkeyAuthentication yes/' /etc/ssh/sshd_config

# Применяем изменения
systemctl restart sshd

echo "✅ SSH защищен (только ключи, без root)"

# 5. Автоматические обновления безопасности
echo "🔄 Настройка автоматических обновлений..."
apt-get install -y unattended-upgrades apt-listchanges

cat > /etc/apt/apt.conf.d/50unattended-upgrades << 'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF

dpkg-reconfigure -plow unattended-upgrades

echo "✅ Автообновления настроены"

# 6. Docker security
echo "🐳 Защита Docker..."

# Ограничиваем логи Docker
cat > /etc/docker/daemon.json << 'EOF'
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

systemctl restart docker

echo "✅ Docker защищен"

# 7. Установка инструментов мониторинга
echo "📊 Установка инструментов..."
apt-get install -y htop iotop netstat-nat sysstat

# 8. Настройка ротации логов
cat > /etc/logrotate.d/money_bot << 'EOF'
/opt/money_bot/*.log {
    daily
    rotate 7
    compress
    missingok
    notifempty
}
EOF

echo "✅ Ротация логов настроена"

# 9. Проверка открытых портов
echo ""
echo "📋 Открытые порты:"
ss -tulpn | grep LISTEN

echo ""
echo "🎉 Защита VPS завершена!"
echo ""
echo "⚠️ ВАЖНО: Убедись что у пользователя kimster есть SSH ключ!"
echo "   Иначе не сможешь зайти после перезагрузки!"
echo ""
echo "Проверь: cat ~/.ssh/authorized_keys"
echo ""

