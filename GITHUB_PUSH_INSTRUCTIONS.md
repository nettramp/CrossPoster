# Инструкция по отправке изменений на GitHub

## Статус изменений

Изменения уже были зафиксированы локально в коммите с сообщением:
- "Add Docker setup instructions and fix for cross-posting error"

## Возможные причины ошибки при отправке на GitHub

1. Проблемы с аутентификацией токена GitHub
2. Устаревший токен доступа
3. Ограничения безопасности на уровне системы

## Решения

### Вариант 1: Проверка токена

1. Убедитесь, что ваш токен GitHub имеет права на запись в репозиторий
2. Проверьте, что токен не истек и не был отозван

### Вариант 2: Переустановка аутентификации

Выполните следующие команды в терминале:

```bash
# Удалить текущую настройку аутентификации
git config --unset-all credential.helper

# Установить новый URL с действительным токеном
git remote set-url origin https://<ваш_токен_здесь>@github.com/nettramp/CrossPoster.git

# Попробовать отправить изменения
git push origin main
```

### Вариант 3: Использование SSH вместо HTTPS

1. Сгенерируйте SSH-ключ:
```bash
ssh-keygen -t ed25519 -C "ваш_email@example.com"
```

2. Добавьте ключ в ssh-agent:
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

3. Добавьте SSH-ключ в свой аккаунт GitHub через веб-интерфейс

4. Измените URL репозитория на SSH:
```bash
git remote set-url origin git@github.com:nettramp/CrossPoster.git
```

5. Попробуйте отправить изменения:
```bash
git push origin main
```

### Вариант 4: Использование Git Credential Manager

Если установлен Git Credential Manager, вы можете выполнить:

```bash
# Для Windows
git config --global credential.helper manager-core

# Для macOS
git config --global credential.helper osxkeychain

# Для Linux
git config --global credential.helper cache

# Затем выполните push - вас попросят ввести учетные данные
git push origin main
```

## Подробности о внесенных изменениях

В результате выполнения задачи были:

1. Пересобран и запущен проект в Docker
2. Исправлена ошибка 500 при попытке выполнить кросс-постинг
3. Добавлены инструкции по настройке и запуску проекта в Docker
4. Создан файл `DOCKER_SETUP_INSTRUCTIONS.md` с подробной документацией

Файл `DOCKER_SETUP_INSTRUCTIONS.md` содержит:
- Команды для запуска проекта в Docker
- Описание проблемы с ошибкой 500 при кросс-постинге
- Решение проблемы с отсутствием активных аккаунтов в базе данных
- SQL-запросы для добавления тестовых аккаунтов