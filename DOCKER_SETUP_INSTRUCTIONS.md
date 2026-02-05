# Инструкция по запуску проекта в Docker

## Пересборка и запуск проекта

Для пересборки проекта и запуска в Docker выполните команду:

```bash
docker-compose up --build -d
```

## Исправление ошибки 500 при кросс-постинге

При первом запуске проекта может возникнуть ошибка 500 при попытке выполнить кросс-постинг с сообщением:

```
HTTP error! status: 500, message: {"detail":"Ошибка при выполнении кросс-постинга: \nДетали: Traceback (most recent call last):\n  File \"/app/app/api/admin.py\", line 179, in crosspost_posts\n    raise HTTPException(status_code=400, detail=f\"Нет активных аккаунтов для источника: {source_platform}\")\nfastapi.exceptions.HTTPException\n"}
```

### Причина ошибки

Ошибка возникает из-за отсутствия активных аккаунтов в таблице `social_accounts` базы данных.

### Решение

Для решения проблемы необходимо добавить хотя бы один аккаунт в базу данных:

```bash
# Добавление тестового пользователя (если не существует)
docker exec crossposter-db-1 psql -U crossposter -d crossposter -c "INSERT INTO users (id, username, email, password_hash) VALUES (1, 'admin', 'admin@example.com', 'hashed_password') ON CONFLICT (id) DO NOTHING;"

# Добавление тестового аккаунта ВКонтакте
docker exec crossposter-db-1 psql -U crossposter -d crossposter -c "INSERT INTO social_accounts (user_id, platform, account_name, access_token, is_active, settings) VALUES (1, 'vk', 'Тестовая группа ВК', 'test_token', true, '{}');"

# Добавление тестового аккаунта Telegram
docker exec crossposter-db-1 psql -U crossposter -d crossposter -c "INSERT INTO social_accounts (user_id, platform, account_name, access_token, is_active, settings) VALUES (1, 'telegram', 'Тестовый канал Телеграм', 'test_token', true, '{}');"
```

После добавления аккаунтов перезапустите веб-сервис:

```bash
docker-compose restart web
```

Теперь кросс-постинг должен работать корректно.