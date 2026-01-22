"""
Скрипт для инициализации базы данных
"""
import subprocess
import sys
import time
import os

def init_database():
    print("Инициализация базы данных...")
    
    # Ждем пока база данных будет готова
    print("Ожидание запуска PostgreSQL...")
    for i in range(30):
        try:
            result = subprocess.run([
                "docker-compose", "exec", "db", "pg_isready"
            ], capture_output=True, text=True)
            if result.returncode == 0:
                print("PostgreSQL готов к работе")
                break
        except Exception:
            pass
        print(f"Попытка {i+1}/30: PostgreSQL еще не готов...")
        time.sleep(2)
    else:
        print("PostgreSQL не стал доступен в течение 60 секунд")
        return False

    # Проверяем, существует ли пользователь и база данных
    print("Проверка наличия пользователя и базы данных...")
    try:
        subprocess.run([
            "docker-compose", "exec", "db",
            "psql", "-U", "postgres", "-c",
            "SELECT 1 FROM pg_roles WHERE rolname='crossposter'"
        ], check=True, capture_output=True)
        print("Пользователь crossposter существует")
    except subprocess.CalledProcessError:
        print("Создание пользователя crossposter...")
        subprocess.run([
            "docker-compose", "exec", "db",
            "psql", "-U", "postgres", "-c",
            "CREATE USER crossposter WITH PASSWORD 'crossposter';"
        ], check=True)

    try:
        subprocess.run([
            "docker-compose", "exec", "db",
            "psql", "-U", "postgres", "-c",
            "SELECT 1 FROM pg_database WHERE datname='crossposter'"
        ], check=True, capture_output=True)
        print("База данных crossposter существует")
    except subprocess.CalledProcessError:
        print("Создание базы данных crossposter...")
        subprocess.run([
            "docker-compose", "exec", "db",
            "psql", "-U", "postgres", "-c",
            "CREATE DATABASE crossposter OWNER crossposter;"
        ], check=True)

    # Запускаем миграции
    print("Запуск миграций Alembic...")
    try:
        subprocess.run([
            "docker-compose", "exec", "web",
            "alembic", "upgrade", "head"
        ], check=True)
        print("Миграции успешно применены")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при применении миграций: {e}")
        return False

    return True

if __name__ == "__main__":
    success = init_database()
    if success:
        print("Инициализация базы данных завершена успешно")
        # Перезапускаем веб-контейнер
        subprocess.run(["docker-compose", "restart", "web"])
    else:
        print("Ошибка инициализации базы данных")
        sys.exit(1)