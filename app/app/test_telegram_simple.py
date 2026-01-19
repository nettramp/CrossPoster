import sys
sys.path.append('/app')

from app.core.config import settings
from telegram import Bot
import asyncio

def test_telegram_simple():
    try:
        # Инициализируем Telegram бота
        bot = Bot(token=settings.telegram_bot_token)
        
        # Отправляем тестовое сообщение в ваш канал
        chat_id = "@CrossPoster68"
        message = "Test message from CrossPoster"
        
        # Асинхронный вызов в синхронной функции
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(bot.send_message(chat_id=chat_id, text=message))
        loop.close()
        
        print(f"Telegram test result: {result}")
        print(f"Message ID: {result.message_id}")
        print(f"Message date: {result.date}")
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    test_telegram_simple()