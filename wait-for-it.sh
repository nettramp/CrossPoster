#!/bin/sh

# Использование: wait-for-it.sh host:port [command]
# Ожидание готовности хоста и порта, затем выполнение команды

TIMEOUT=60
HOST_PORT=$1
shift

# Функция для проверки доступности хоста и порта
wait_for_port() {
    local host=$(echo $1 | cut -d: -f1)
    local port=$(echo $1 | cut -d: -f2)
    
    echo "Ожидание готовности $host:$port..."
    
    local start_ts=$(date +%s)
    while :
    do
        if nc -z "$host" "$port" 2>/dev/null; then
            echo "$host:$port готов!"
            break
        fi
        
        sleep 1
        
        local elapsed_ts=$(date +%s)
        if [ $((elapsed_ts - start_ts)) -gt $TIMEOUT ]; then
            echo "Таймаут ожидания $host:$port"
            exit 1
        fi
    done
}

wait_for_port $HOST_PORT

# Выполнение команды, если она предоставлена
if [ $# -gt 0 ]; then
    exec "$@"
fi