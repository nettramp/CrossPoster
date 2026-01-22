# Деплой CrossPoster на продакшен

## Подготовка сервера

1. Создайте Ubuntu 22.04 сервер
2. Обновите систему:
```bash
sudo apt update && sudo apt upgrade -y
```

3. Установите Docker и Docker Compose:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

4. Установите Python и pip:
```bash
sudo apt install python3-pip python3-dev python3-venv -y
```

## Настройка приложения

1. Клонируйте репозиторий:
```bash
git clone https://github.com/ваш-аккаунт/crossposter.git
cd crossposter
```

2. Создайте файл `.env` с вашими настройками:
```bash
cp .env.example .env
nano .env
```

3. Установите переменные окружения:
```
# База данных
DATABASE_URL=postgresql://crossposter:password@localhost:5432/crossposter
POSTGRES_DB=crossposter
POSTGRES_USER=crossposter
POSTGRES_PASSWORD=your_secure_password

# Redis
REDIS_URL=redis://localhost:6379/0

# Безопасность
SECRET_KEY=your_very_long_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here

# API ключи будут добавлены через веб-интерфейс
VK_API_TOKEN=
TELEGRAM_BOT_TOKEN=
```

4. Установите и настройте PostgreSQL:
```bash
sudo apt install postgresql postgresql-contrib -y
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Создайте пользователя и базу данных
sudo -u postgres psql << EOF
CREATE USER crossposter WITH PASSWORD 'your_secure_password';
CREATE DATABASE crossposter OWNER crossposter;
ALTER USER crossposter CREATEDB;
\q
EOF
```

5. Установите и настройте Redis:
```bash
sudo apt install redis-server -y
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

## Запуск приложения

1. Запустите приложение с помощью Docker Compose:
```bash
docker-compose up -d
```

2. Проверьте статус сервисов:
```bash
docker-compose ps
```

## Безопасное добавление API-ключей

1. Откройте веб-интерфейс приложения в браузере: `http://your-server-ip:8000`

2. Перейдите на страницу подключения аккаунтов

3. Введите API-ключи через веб-интерфейс - они будут зашифрованы и безопасно сохранены в базе данных

## Тестирование репоста

1. После подключения аккаунтов используйте кнопку "Тестовый репост" на главной странице

2. Введите тестовое сообщение и, при необходимости, прикрепите медиафайлы

3. Нажмите "Отправить тестовый репост" для проверки работы системы

## Настройка SSL (рекомендуется)

1. Установите Certbot:
```bash
sudo apt install certbot python3-certbot-nginx -y
```

2. Настройте Nginx (создайте файл `/etc/nginx/sites-available/crossposter`):
```
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

3. Активируйте сайт и получите SSL-сертификат:
```bash
sudo ln -s /etc/nginx/sites-available/crossposter /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
sudo certbot --nginx -d your-domain.com
```

## Мониторинг и обслуживание

1. Проверка статуса приложения:
```bash
docker-compose logs web
docker-compose logs worker
docker-compose logs scheduler
```

2. Регулярные обновления:
```bash
git pull origin main
docker-compose build --no-cache
docker-compose up -d
```

3. Резервное копирование:
```bash
# База данных
sudo -u postgres pg_dump crossposter > backup_$(date +%Y%m%d_%H%M%S).sql

# Конфигурационные файлы
tar -czf config_backup_$(date +%Y%m%d_%H%M%S).tar.gz .env docker-compose.yml
```

## Безопасность

- Все API-ключи хранятся в зашифрованном виде
- Веб-интерфейс позволяет безопасно вводить ключи без риска их утечки в коде
- Регулярно обновляйте систему и приложение
- Используйте SSL для защиты трафика
- Ограничьте доступ к серверу через SSH ключи