#!/bin/bash

# Скрипт для запуска приложения CrossPoster

# Создание директории для медиафайлов
mkdir -p media

# Применение миграций базы данных
echo "Applying database migrations..."
alembic upgrade head

# Запуск веб-сервера
echo "Starting web server..."
uvicorn app.main:app --host 0.0.0.0 --port 8000