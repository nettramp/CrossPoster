#!/bin/bash

# Скрипт для запуска приложения CrossPoster

set -e  # Выход при ошибке

# Создание директории для медиафайлов
mkdir -p media

# Применение миграций базы данных
echo "Applying database migrations..."
if command -v alembic &> /dev/null; then
    alembic upgrade head
else
    echo "Alembic not found, installing dependencies..."
    pip install -r requirements.txt
    alembic upgrade head
fi

# Запуск веб-сервера
echo "Starting web server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000