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
        
        # Обрабатываем посты для извлечения медиа
        processed_posts = []
        for post in posts:
            processed_post = {
                'id': post.get('id'),
                'text': post.get('text', ''),
                'date': post.get('date'),
                'media': []
            }
            
            # Обрабатываем вложения
            if 'attachments' in post:
                for attachment in post['attachments']:
                    if attachment['type'] == 'photo':
                        # Берем фото самого большого размера
                        sizes = attachment['photo']['sizes']
                        max_size_photo = max(sizes, key=lambda x: x['width'])
                        processed_post['media'].append(max_size_photo['url'])
                    elif attachment['type'] == 'video':
                        # Для видео добавляем ссылку на видео (если доступна)
                        if 'player' in attachment['video']:
                            processed_post['media'].append(attachment['video']['player'])
            
            processed_posts.append(processed_post)
        
        return {"status": "success", "posts": processed_posts}
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
        
        # Обрабатываем медиафайлы
        attachments = []
        if 'media' in post_data and post_data['media']:
            for media_item in post_data['media']:
                # Скачиваем медиафайл
                import uuid
                from app.utils.media_downloader import download_media, get_file_extension
                
                file_extension = get_file_extension(media_item)
                temp_filename = f"/tmp/{uuid.uuid4()}.{file_extension}"
                
                downloaded_path = download_media(media_item, temp_filename)
                if downloaded_path:
                    # Загружаем в VK
                    attachment = vk_client.upload_photo(downloaded_path)
                    if attachment:
                        attachments.append(attachment)
        
        result = vk_client.post_to_wall(owner_id, post_data['text'], attachments)
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@celery_app.task
def send_test_post_to_all_platforms(post_data: dict, accounts_data: list):
    """
    Отправить тестовый пост во все подключенные платформы
    """
    results = {}
    
    for account in accounts_data:
        try:
            platform = account['platform']
            access_token = account['access_token']
            settings = account.get('settings', {})
            
            if platform == 'vk':
                vk_client = VKClient(access_token)
                result = vk_client.post_to_wall(
                    owner_id=settings.get('group_id', ''),
                    message=post_data['content'],
                    attachments=post_data.get('media')
                )
                results[f"vk_{account['id']}"] = {"success": True, "result": result}
                
            elif platform == 'telegram':
                telegram_client = TelegramClient(access_token)
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    telegram_client.post_to_channel(
                        chat_id=settings.get('channel', ''),
                        text=post_data['content'],
                        media=post_data.get('media')
                    )
                )
                loop.close()
                results[f"telegram_{account['id']}"] = {"success": True, "result": result}
                
            elif platform == 'instagram':
                instagram_client = InstagramClient(
                    account['username'],
                    access_token  # в данном случае access_token содержит логин:пароль
                )
                result = instagram_client.post_content(
                    content=post_data['content'],
                    media_urls=post_data.get('media', [])
                )
                results[f"instagram_{account['id']}"] = {"success": True, "result": result}
                
            elif platform == 'pinterest':
                pinterest_client = PinterestClient(access_token)
                result = pinterest_client.post_pin(
                    board=settings.get('board', ''),
                    note=post_data['content'],
                    media_url=post_data.get('media', [None])[0] if post_data.get('media') else None
                )
                results[f"pinterest_{account['id']}"] = {"success": True, "result": result}
                
            elif platform == 'youtube':
                youtube_client = YouTubeClient(access_token)
                result = youtube_client.upload_short(
                    title=f"Тестовый пост: {post_data['content'][:50]}...",
                    description=post_data['content'],
                    media_path=post_data.get('media', [None])[0] if post_data.get('media') else None
                )
                results[f"youtube_{account['id']}"] = {"success": True, "result": result}
                
        except Exception as e:
            results[f"{platform}_{account['id']}"] = {"success": False, "error": str(e)}
    
    return {"status": "complete", "results": results}

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
        
        # Обрабатываем медиафайлы для Telegram
        # (уже реализовано в telegram_client.py)
        loop.close()
        
        return {"status": "success", "result": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}