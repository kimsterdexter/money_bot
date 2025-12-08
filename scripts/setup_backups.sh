#!/bin/bash

# Скрипт настройки автоматических бэкапов БД
# Выполнять от пользователя kimster

set -e

BACKUP_DIR="/home/kimster/backups"
SCRIPT_PATH="/home/kimster/backup_db.sh"

echo "💾 Настройка автоматических бэкапов..."
echo ""

# 1. Создаем директорию для бэкапов
mkdir -p $BACKUP_DIR

# 2. Создаем скрипт бэкапа
cat > $SCRIPT_PATH << 'EOFSCRIPT'
#!/bin/bash

BACKUP_DIR="/home/kimster/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/money_bot_$DATE.sql"

# Бэкап базы данных
docker exec money_bot_db pg_dump -U postgres money_bot > $BACKUP_FILE 2>/dev/null

if [ $? -eq 0 ]; then
    # Сжимаем
    gzip $BACKUP_FILE
    echo "✅ Backup created: ${BACKUP_FILE}.gz"
    
    # Удаляем старые бэкапы (старше 30 дней)
    find $BACKUP_DIR -name "money_bot_*.sql.gz" -mtime +30 -delete
    
    # Проверяем размер всех бэкапов
    TOTAL_SIZE=$(du -sh $BACKUP_DIR | cut -f1)
    echo "📊 Total backups size: $TOTAL_SIZE"
else
    echo "❌ Backup failed!"
    exit 1
fi
EOFSCRIPT

chmod +x $SCRIPT_PATH

# 3. Тестовый запуск
echo "🧪 Тестовый бэкап..."
$SCRIPT_PATH

# 4. Добавляем в crontab (каждый день в 3:00)
echo "⏰ Настройка автоматического расписания..."

# Проверяем есть ли уже в crontab
if crontab -l 2>/dev/null | grep -q "backup_db.sh"; then
    echo "⚠️ Задача уже существует в crontab"
else
    (crontab -l 2>/dev/null; echo "0 3 * * * $SCRIPT_PATH >> /home/kimster/backup.log 2>&1") | crontab -
    echo "✅ Добавлено в crontab: ежедневно в 3:00"
fi

# 5. Показываем текущие задачи
echo ""
echo "📋 Текущие задачи cron:"
crontab -l | grep backup_db || echo "Нет задач"

echo ""
echo "🎉 Автоматические бэкапы настроены!"
echo ""
echo "📂 Директория бэкапов: $BACKUP_DIR"
echo "📜 Логи: /home/kimster/backup.log"
echo ""
echo "Команды для управления:"
echo "  - Ручной бэкап: $SCRIPT_PATH"
echo "  - Список бэкапов: ls -lh $BACKUP_DIR"
echo "  - Восстановление: gunzip -c backup.sql.gz | docker exec -i money_bot_db psql -U postgres -d money_bot"
echo ""

