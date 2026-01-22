#!/bin/sh

# Ожидание готовности PostgreSQL
TIMEOUT=60
DB_HOST="db"
DB_PORT="5432"
DB_USER="crossposter"
DB_NAME="crossposter"

echo "Ожидание готовности PostgreSQL..."

start_ts=$(date +%s)
while :
do
    # Проверяем, можно ли подключиться к базе данных
    if python3 -c "import psycopg2; psycopg2.connect(host='$DB_HOST', port='$DB_PORT', user='$DB_USER', password='crossposter', database='$DB_NAME')" 2>/dev/null; then
        echo "PostgreSQL готов!"
        break
    fi

    sleep 2

    elapsed_ts=$(date +%s)
    if [ $((elapsed_ts - start_ts)) -gt $TIMEOUT ]; then
        echo "Таймаут ожидания PostgreSQL"
        exit 1
    fi

    echo "Ожидание готовности PostgreSQL..."
done

# Выполнение команды, если она предоставлена
if [ $# -gt 0 ]; then
    exec "$@"
fi