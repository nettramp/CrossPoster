#!/usr/bin/env python3
"""
Тестовый скрипт для проверки отправки сообщения и фото в Telegram напрямую
"""
import asyncio
import os
from app.social.telegram_client import TelegramClient

async def test_telegram_post():
    # Получаем токен и ID чата из переменных окружения или просим пользователя ввести
    bot_token = input("Введите токен Telegram бота: ").strip()
    chat_id = input("Введите ID чата/канала в Telegram: ").strip()
    
    # Создаем экземпляр клиента
    client = TelegramClient(bot_token)
    
    # Текст тестового сообщения
    text = "Тестовое сообщение от CrossPoster!"
    
    # URL тестового изображения
    test_image_url = "https://via.placeholder.com/600x400.png?text=Test+Image"
    
    print(f"Отправка тестового сообщения в чат {chat_id}...")
    print(f"Текст: {text}")
    print(f"Изображение: {test_image_url}")
    
    try:
        # Отправляем сообщение с изображением
        result = await client.post_to_channel(
            chat_id=chat_id,
            text=text,
            media=[test_image_url]
        )
        
        print("Успешно отправлено!")
        print(f"Результат: {result}")
        
    except Exception as e:
        print(f"Ошибка при отправке: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_telegram_post())