#!/usr/bin/env python3
"""
Скрипт для отладки Telegram клиента
"""
import asyncio
import tempfile
import os
from urllib.parse import urlparse
from app.social.telegram_client import TelegramClient
from app.utils.media_downloader import download_media

async def debug_telegram_post():
    # Ваши тестовые данные
    bot_token = os.getenv('TELEGRAM_BOT_TOKEN', 'YOUR_BOT_TOKEN_HERE')
    chat_id = os.getenv('TELEGRAM_CHAT_ID', 'YOUR_CHAT_ID_HERE')
    
    # Проверяем, что токен и чат ID заданы
    if bot_token == 'YOUR_BOT_TOKEN_HERE' or chat_id == 'YOUR_CHAT_ID_HERE':
        print("Ошибка: Необходимо задать TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID")
        print("Вы можете задать их как переменные окружения или изменить в коде.")
        return
    
    # Создаем экземпляр клиента
    client = TelegramClient(bot_token)
    
    # Текст тестового сообщения
    text = "Тестовое сообщение от CrossPoster!"
    
    # URL тестового изображения
    test_image_url = "https://via.placeholder.com/600x400.png?text=Test+Image"
    
    print(f"Отладка отправки в чат {chat_id}...")
    print(f"Текст: {text}")
    print(f"URL изображения: {test_image_url}")
    
    # Проверим, что URL корректный
    parsed = urlparse(test_image_url)
    if not parsed.scheme or not parsed.netloc:
        print(f"Некорректный URL: {test_image_url}")
        return
    
    try:
        # Попробуем скачать изображение
        print("\n1. Попытка скачать изображение...")
        with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
            tmp_filename = tmp_file.name
        
        downloaded_path = download_media(test_image_url, tmp_filename)
        if downloaded_path:
            print(f"Изображение успешно скачано: {downloaded_path}")
            
            # Теперь попробуем отправить через файл
            print("\n2. Попытка отправить через локальный файл...")
            with open(downloaded_path, 'rb') as f:
                if test_image_url.lower().endswith(('.jpg', '.jpeg', '.png', '.gif')):
                    result = await client.bot.send_photo(chat_id=chat_id, photo=f, caption=text)
                    print("Успешно отправлено как фото!")
                    print(f"Message ID: {result.message_id}")
                else:
                    result = await client.bot.send_document(chat_id=chat_id, document=f, caption=text)
                    print("Успешно отправлено как документ!")
                    print(f"Message ID: {result.message_id}")
            
            # Удалим временный файл
            os.unlink(downloaded_path)
        else:
            print("Не удалось скачать изображение")
            
    except Exception as e:
        print(f"Ошибка при работе с изображением: {str(e)}")
        import traceback
        traceback.print_exc()

    # Также проверим, можно ли отправить напрямую через URL (новый способ)
    print("\n3. Попытка отправить напрямую через URL...")
    try:
        result = await client.post_to_channel(
            chat_id=chat_id,
            text=text,
            media=[test_image_url]
        )
        print("Успешно отправлено через URL!")
        print(f"Результат: {result}")
    except Exception as e:
        print(f"Ошибка при отправке через URL: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_telegram_post())