import sys
sys.path.append('/app')

from app.social.telegram_client import TelegramClient
from app.core.config import settings
import asyncio

async def test_telegram():
    try:
        # Инициализируем Telegram клиент
        tg = TelegramClient(settings.telegram_bot_token)
        
        # Отправляем тестовое сообщение
        # Замените @nettramp_test на ваш Telegram канал
        result = await tg.post_to_channel('@nettramp_test', 'Test message from CrossPoster')
        print(f"Telegram test result: {result}")
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(test_telegram())