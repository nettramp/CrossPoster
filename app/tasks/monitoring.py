import asyncio
from celery import Celery
from app.core.config import settings
from app.social.vk_client import VKClient
from app.social.telegram_client import TelegramClient
from app.social.instagram_client import InstagramClient
from app.social.pinterest_client import PinterestClient
from app.social.youtube_client import YouTubeClient

# Инициализация Celery
celery_app = Celery("crossposter", broker=settings.redis_url)

@celery_app.task
def check_vk_posts(account_id: int, access_token: str, owner_id: str):
    """Проверить новые посты в VK"""
    try:
        vk_client = VKClient(access_token)
        posts = vk_client.get_latest_posts(owner_id, count=5)
        
        # TODO: Проверить, какие посты уже были обработаны
        # TODO: Отправить новые посты в очередь для репоста
        
        return {"status": "success", "posts_count": len(posts)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@celery_app.task
def check_telegram_posts(account_id: int, bot_token: str, chat_id: str):
    """Проверить новые посты в Telegram"""
    try:
        telegram_client = TelegramClient(bot_token)
        
        # Асинхронный вызов в синхронной функции
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        posts = loop.run_until_complete(telegram_client.get_latest_posts(chat_id, limit=5))
        loop.close()
        
        # TODO: Проверить, какие посты уже были обработаны
        # TODO: Отправить новые посты в очередь для репоста
        
        return {"status": "success", "posts_count": len(posts)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@celery_app.task
def check_instagram_posts(account_id: int, username: str, password: str, user_id: str):
    """Проверить новые посты в Instagram"""
    try:
        instagram_client = InstagramClient(username, password)
        posts = instagram_client.get_latest_posts(user_id, count=5)
        
        # TODO: Проверить, какие посты уже были обработаны
        # TODO: Отправить новые посты в очередь для репоста
        
        return {"status": "success", "posts_count": len(posts)}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@celery_app.task
def repost_to_vk(post_data: dict, access_token: str, owner_id: str):
    """Репостить контент в VK"""
    try:
        vk_client = VKClient(access_token)
        
        # TODO: Обработать медиафайлы
        attachments = []
        if 'media' in post_data:
            for media_url in post_data['media']:
                # TODO: Скачать медиа и загрузить в VK
                pass
        
        result = vk_client.post_to_wall(owner_id, post_data['text'], attachments)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@celery_app.task
def repost_to_telegram(post_data: dict, bot_token: str, chat_id: str):
    """Репостить контент в Telegram"""
    try:
        telegram_client = TelegramClient(bot_token)
        
        # Асинхронный вызов в синхронной функции
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            telegram_client.post_to_channel(chat_id, post_data['text'], post_data.get('media'))
        )
        loop.close()
        
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}