import sys
sys.path.append('/app')

from app.core.config import settings
from telegram import Bot

def test_telegram_sync():
    try:
        # Инициализируем Telegram бота
        bot = Bot(token=settings.telegram_bot_token)
        
        # Отправляем тестовое сообщение в ваш канал
        chat_id = "@CrossPoster68"
        message = "Test message from CrossPoster (sync)"
        
        # Синхронный вызов
        result = bot.send_message(chat_id=chat_id, text=message)
        
        print(f"Telegram test result: {result}")
        print(f"Message ID: {result.message_id}")
        print(f"Message date: {result.date}")
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    test_telegram_sync()