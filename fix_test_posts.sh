#!/bin/bash

echo "=== Исправление проблемы с тестовыми сообщениями ==="

echo "1. Остановка всех контейнеров..."
docker-compose down

echo "2. Проверка наличия переменной ENCRYPTION_KEY в .env файле..."
if ! grep -q "ENCRYPTION_KEY=" .env; then
    echo "Переменная ENCRYPTION_KEY отсутствует в .env файле. Добавляем..."
    ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
    echo "ENCRYPTION_KEY=$ENCRYPTION_KEY" >> .env
    echo "Добавлен новый ключ шифрования в .env файл"
else
    echo "Переменная ENCRYPTION_KEY уже существует в .env файле"
fi

echo "3. Сброс зашифрованных токенов в базе данных..."
docker-compose up -d db
sleep 5
docker-compose exec db psql -U crossposter -d crossposter -c "UPDATE social_accounts SET access_token = '', refresh_token = '';"
docker-compose down

echo "4. Перезапуск всех сервисов..."
docker-compose up -d

echo "5. Ожидание запуска сервисов..."
sleep 10

echo "=== Исправление завершено ==="
echo ""
echo "Теперь вы можете:"
echo "1. Открыть веб-интерфейс по адресу http://localhost:8000"
echo "2. Перейти в раздел 'Аккаунты' (http://localhost:8000/accounts)"
echo "3. Ввести действительные токены для ваших аккаунтов VK и Telegram"
echo "4. Проверить отправку тестового сообщения"
echo ""
echo "Если проблема сохраняется, проверьте логи воркера командой:"
echo "docker-compose logs worker"