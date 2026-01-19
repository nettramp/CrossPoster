import sys
sys.path.append('/app')

from app.core.config import settings
from telegram import Bot
import asyncio

async def test_telegram_async():
    try:
        # Инициализируем Telegram бота
        bot = Bot(token=settings.telegram_bot_token)
        
        # Отправляем тестовое сообщение в ваш канал
        chat_id = "@CrossPoster68"
        message = "Test message from CrossPoster (async)"
        
        # Асинхронный вызов
        result = await bot.send_message(chat_id=chat_id, text=message)
        
        print(f"Telegram test result: {result}")
        print(f"Message ID: {result.message_id}")
        print(f"Message date: {result.date}")
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

def test_telegram():
    # Запускаем асинхронную функцию
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(test_telegram_async())
    loop.close()
    return result

if __name__ == "__main__":
    test_telegram()