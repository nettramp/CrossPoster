# Развёртывание CrossPoster на сервере Ubuntu 22.04

## Подготовка сервера

1. Подключитесь к вашему серверу по SSH:
   ```bash
   ssh nettramp@10.211.55.3
   ```

2. Обновите систему:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```

## Клонирование репозитория

1. Установите Git, если он ещё не установлен:
   ```bash
   sudo apt install git -y
   ```

2. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/nettramp/CrossPoster.git
   cd CrossPoster
   ```

## Настройка окружения

1. Создайте файл `.env` на основе примера:
   ```bash
   cp .env.example .env
   ```

2. Отредактируйте файл `.env`, добавив ваши токены и ключи:
   ```bash
   nano .env
   ```

   Необходимо заполнить следующие параметры:
   - VK_API_TOKEN
   - TELEGRAM_BOT_TOKEN
   - INSTAGRAM_USERNAME и INSTAGRAM_PASSWORD
   - PINTEREST_API_KEY
   - YOUTUBE_API_KEY
   - SECRET_KEY (сгенерируйте случайную строку)

## Развёртывание с помощью Docker Compose

1. Убедитесь, что Docker и Docker Compose установлены:
   ```bash
   docker --version
   docker-compose --version
   ```

2. Запустите приложение:
   ```bash
   docker-compose up -d
   ```

3. Примените миграции базы данных:
   ```bash
   docker-compose exec web alembic upgrade head
   ```

## Проверка работы

1. Проверьте статус контейнеров:
   ```bash
   docker-compose ps
   ```

2. Проверьте логи приложения:
   ```bash
   docker-compose logs web
   ```

3. Приложение будет доступно по адресу:
   ```
   http://10.211.55.3:8000
   ```

## Управление приложением

- Остановка приложения:
  ```bash
  docker-compose down
  ```

- Перезапуск приложения:
  ```bash
  docker-compose restart
  ```

- Просмотр логов:
  ```bash
  docker-compose logs -f
  ```

## Настройка автозапуска

Для автоматического запуска приложения после перезагрузки сервера, добавьте следующую строку в crontab:

```bash
@reboot cd /home/nettramp/CrossPoster && docker-compose up -d
```

Откройте crontab для редактирования:
```bash
crontab -e
```

И добавьте указанную выше строку.

## Обновление приложения

Для обновления приложения до последней версии из репозитория:

1. Остановите приложение:
   ```bash
   docker-compose down
   ```

2. Получите последние изменения:
   ```bash
   git pull
   ```

3. Пересоберите контейнеры:
   ```bash
   docker-compose up --build -d
   ```

4. Примените миграции базы данных (если есть):
   ```bash
   docker-compose exec web alembic upgrade head