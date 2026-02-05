# Развёртывание CrossPoster

## Подготовка Ubuntu 22.04 сервера для запуска CrossPoster

### 1. Обновление системы и установка необходимых пакетов

```bash
sudo apt update
sudo apt upgrade -y

# Установка Python 3.10 и pip
sudo apt install -y python3.10 python3.10-dev python3.10-venv python3-pip

# Установка системных зависимостей
sudo apt install -y build-essential libpq-dev postgresql postgresql-contrib redis-server git curl nginx supervisor

# Установка Docker и Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Установка Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Настройка PostgreSQL

```bash
# Запуск PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Создание пользователя и базы данных
sudo -u postgres psql << EOF
CREATE USER crossposter WITH PASSWORD 'strong_password_here';
CREATE DATABASE crossposter OWNER crossposter;
ALTER USER crossposter CREATEDB;
\q
EOF
```

### 3. Настройка Redis

```bash
# Запуск Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 4. Клонирование репозитория и установка приложения

```bash
# Клонирование репозитория
cd /home/$USER
git clone https://github.com/nettramp/CrossPoster.git
cd CrossPoster

# Создание виртуального окружения
python3.10 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Настройка конфигурации

Создайте файл `.env` с вашими API-ключами:

```bash
cp .env.example .env
nano .env  # Отредактируйте файл и укажите свои API-ключи
```

Обязательно измените следующие параметры в `.env`:
```
DATABASE_URL=postgresql://crossposter:strong_password_here@localhost:5432/crossposter
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=very_strong_secret_key_here
ENCRYPTION_KEY=your_encryption_key_here
```

**Важно:** Переменная `ENCRYPTION_KEY` должна быть установлена и сохранена неизменной, так как она используется для шифрования и расшифровки API-токенов. Если ключ изменится, все ранее сохраненные токены станут недействительными.

### 6. Запуск миграций базы данных

```bash
alembic upgrade head
```

### 7. Настройка Supervisor для запуска приложений

Создайте файл `/etc/supervisor/conf.d/crossposter-web.conf`:

```bash
sudo nano /etc/supervisor/conf.d/crossposter-web.conf
```

Содержимое файла:
```
[program:crossposter-web]
command=/home/USER/CrossPoster/venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
directory=/home/USER/CrossPoster
user=USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/crossposter/web.log
environment=PATH="/home/USER/CrossPoster/venv/bin"
```

Замените `USER` на имя вашего пользователя.

Создайте файл `/etc/supervisor/conf.d/crossposter-worker.conf`:

```bash
sudo nano /etc/supervisor/conf.d/crossposter-worker.conf
```

Содержимое файла:
```
[program:crossposter-worker]
command=/home/USER/CrossPoster/venv/bin/celery -A app.worker worker --loglevel=info
directory=/home/USER/CrossPoster
user=USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/crossposter/worker.log
environment=PATH="/home/USER/CrossPoster/venv/bin"
```

Создайте файл `/etc/supervisor/conf.d/crossposter-scheduler.conf`:

```bash
sudo nano /etc/supervisor/conf.d/crossposter-scheduler.conf
```

Содержимое файла:
```
[program:crossposter-scheduler]
command=/home/USER/CrossPoster/venv/bin/python -m app.scheduler
directory=/home/USER/CrossPoster
user=USER
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/crossposter/scheduler.log
environment=PATH="/home/USER/CrossPoster/venv/bin"
```

Создайте директории для логов:

```bash
sudo mkdir -p /var/log/crossposter
sudo chown $USER:$USER /var/log/crossposter
```

Перезапустите Supervisor:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start crossposter-web
sudo supervisorctl start crossposter-worker
sudo supervisorctl start crossposter-scheduler
```

### 8. Настройка Nginx

Создайте файл конфигурации `/etc/nginx/sites-available/crossposter`:

```bash
sudo nano /etc/nginx/sites-available/crossposter
```

Содержимое файла (замените `your_domain.com` на ваш домен):
```
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Активируйте сайт:

```bash
sudo ln -s /etc/nginx/sites-available/crossposter /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 9. Настройка SSL (опционально, рекомендуется)

Установите Certbot:

```bash
sudo apt install certbot python3-certbot-nginx -y
```

Получите SSL-сертификат:

```bash
sudo certbot --nginx -d your_domain.com
```

### 10. Автоматическое обновление приложения

Создайте скрипт для обновления приложения:

```bash
nano ~/update_crossposter.sh
```

Содержимое файла:
```bash
#!/bin/bash
cd /home/$USER/CrossPoster

# Резервное копирование
DATE=$(date +%Y%m%d_%H%M%S)
cp .env .env.backup.$DATE

# Обновление кода
git pull origin main

# Активация виртуального окружения
source venv/bin/activate

# Обновление зависимостей
pip install -r requirements.txt

# Применение миграций
alembic upgrade head

# Перезапуск приложений
sudo supervisorctl restart crossposter-web
sudo supervisorctl restart crossposter-worker
sudo supervisorctl restart crossposter-scheduler
```

Сделайте скрипт исполняемым:

```bash
chmod +x ~/update_crossposter.sh
```

### 11. Мониторинг и обслуживание

Проверить статус служб:
```bash
sudo supervisorctl status
```

Просмотреть логи:
```bash
tail -f /var/log/crossposter/web.log
tail -f /var/log/crossposter/worker.log
tail -f /var/log/crossposter/scheduler.log
```

### 12. Резервное копирование

Создайте скрипт резервного копирования:

```bash
crontab -e
```

Добавьте строку для ежедневного резервного копирования в 2:00:
```
0 2 * * * pg_dump -U crossposter crossposter > /home/USER/backups/db_backup_$(date +\%Y\%m\%d).sql
```

Создайте директорию для бэкапов:
```bash
mkdir -p /home/$USER/backups
```

### 13. Настройка безопасности

1. Настройте firewall:
```bash
sudo ufw enable
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
```

2. Настройте fail2ban:
```bash
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

Поздравляем! Ваш CrossPoster успешно установлен и запущен на сервере.