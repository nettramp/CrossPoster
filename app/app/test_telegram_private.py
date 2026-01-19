import sys
sys.path.append('/app')

from app.social.telegram_client import TelegramClient
from app.core.config import settings
import asyncio

async def test_telegram_private():
    try:
        # Инициализируем Telegram клиент
        tg = TelegramClient(settings.telegram_bot_token)
        
        # Получаем информацию о боте
        me = tg.bot.get_me()
        print(f"Bot: {me.username} (ID: {me.id})")
        
        # Отправляем тестовое сообщение в личный чат
        # Для этого нам нужно знать chat_id пользователя
        # Пока просто попробуем отправить сообщение самому себе (боту)
        result = await tg.bot.send_message(chat_id=me.id, text='Test message from CrossPoster')
        print(f"Telegram test result: {result}")
        return result
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    asyncio.run(test_telegram_private())