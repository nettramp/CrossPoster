import asyncio
import sys
import os

# Добавляем путь к приложению
sys.path.append('/app')

from app.core.config import settings
from telegram import Bot

async def check_telegram_api():
    try:
        bot = Bot(token=settings.telegram_bot_token)
        me = bot.get_me()
        print(f"Telegram bot: {me.username}")
        print(f"Bot ID: {me.id}")
        bot.close()
        return True
    except Exception as e:
        print(f"Telegram API connection failed: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(check_telegram_api())