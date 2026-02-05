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
    print(f"Starting send_test_post_to_all_platforms with post_data: {post_data}")
    print(f"Accounts data: {len(accounts_data)} accounts")
    
    results = {}
    
    print(f"Processing {len(accounts_data)} accounts in send_test_post_to_all_platforms")
    for account in accounts_data:
        try:
            platform = account['platform']
            access_token = account['access_token']
            settings = account.get('settings', {})
            
            print(f"Processing account for platform: {platform}, account_id: {account['id']}, token length: {len(access_token) if access_token else 0}")
            
            if platform == 'vk':
                vk_client = VKClient(access_token)
                
                # Проверяем, что обязательные настройки заданы
                if not settings.get('group_id'):
                    error_msg = "Не указан ID группы/пользователя для VK"
                    print(error_msg)
                    results[f"vk_{account['id']}"] = {"success": False, "error": error_msg}
                    continue
                
                attachments = []
                if post_data.get('media'):
                    # Обработка медиафайлов для VK
                    print(f"Processing {len(post_data['media'])} media files for VK")
                    for media_url in post_data['media']:
                        print(f"Downloading media for VK: {media_url}")
                        # Скачиваем и загружаем медиа в VK
                        import uuid
                        from app.utils.media_downloader import download_media, get_file_extension
                        
                        file_extension = get_file_extension(media_url)
                        temp_filename = f"/tmp/{uuid.uuid4()}.{file_extension}"
                        
                        downloaded_path = download_media(media_url, temp_filename)
                        if downloaded_path:
                            print(f"Downloaded media to: {downloaded_path}")
                            # Загружаем в VK
                            attachment = vk_client.upload_photo(downloaded_path, settings.get('group_id'))
                            if attachment:
                                print(f"Uploaded attachment to VK: {attachment}")
                                attachments.append(attachment)
                        else:
                            print(f"Failed to download media: {media_url}")
                
                print(f"Sending post to VK with message: {post_data['content'][:50]}... and {len(attachments)} attachments")
                result = vk_client.post_to_wall(
                    owner_id=str(settings.get('group_id')),
                    message=post_data['content'],
                    attachments=attachments if attachments else None
                )
                
                if 'error' in result:
                    print(f"VK post failed: {result['error']}")
                    results[f"vk_{account['id']}"] = {"success": False, "error": result['error']}
                else:
                    print(f"VK post successful: {result}")
                    results[f"vk_{account['id']}"] = {"success": True, "result": result}
                
            elif platform == 'telegram':
                telegram_client = TelegramClient(access_token)
                
                # Проверяем, что обязательные настройки заданы
                if not settings.get('channel'):
                    error_msg = "Не указан канал для Telegram"
                    print(error_msg)
                    results[f"telegram_{account['id']}"] = {"success": False, "error": error_msg}
                    continue
                
                print(f"Sending post to Telegram with message: {post_data['content'][:50]}... and {len(post_data.get('media', []))} media files")
                # Используем асинхронный вызов в синхронной функции
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    telegram_client.post_to_channel(
                        chat_id=str(settings.get('channel')),
                        text=post_data['content'],
                        media=post_data.get('media')
                    )
                )
                loop.close()
                
                if 'error' in result:
                    print(f"Telegram post failed: {result['error']}")
                    results[f"telegram_{account['id']}"] = {"success": False, "error": result['error']}
                else:
                    print(f"Telegram post successful: {result}")
                    results[f"telegram_{account['id']}"] = {"success": True, "result": result}
                
            elif platform == 'instagram':
                # Для Instagram access_token содержит логин:пароль
                credentials = access_token.split(':')
                if len(credentials) < 2:
                    error_msg = "Неверный формат учетных данных для Instagram (ожидается логин:пароль)"
                    print(error_msg)
                    results[f"instagram_{account['id']}"] = {"success": False, "error": error_msg}
                    continue
                
                instagram_client = InstagramClient(
                    username=credentials[0],
                    password=credentials[1]
                )
                
                # Проверяем тип медиа и вызываем соответствующий метод
                if post_data.get('media'):
                    media_url = post_data['media'][0]  # берем первое медиа
                    print(f"Sending post to Instagram with media: {media_url}")
                    if media_url.endswith(('.mp4', '.mov', '.avi')):
                        # Это видео
                        result = instagram_client.post_video(
                            video_path=media_url,
                            caption=post_data['content']
                        )
                    else:
                        # Это фото
                        result = instagram_client.post_photo(
                            photo_path=media_url,
                            caption=post_data['content']
                        )
                else:
                    # Без медиа не можем опубликовать в Instagram
                    error_msg = "Instagram требует медиафайл для публикации"
                    print(error_msg)
                    results[f"instagram_{account['id']}"] = {"success": False, "error": error_msg}
                    continue
                
                if 'error' in result:
                    print(f"Instagram post failed: {result['error']}")
                    results[f"instagram_{account['id']}"] = {"success": False, "error": result['error']}
                else:
                    print(f"Instagram post successful: {result}")
                    results[f"instagram_{account['id']}"] = {"success": True, "result": result}
                
            elif platform == 'pinterest':
                pinterest_client = PinterestClient(access_token)
                
                # Проверяем, что обязательные настройки заданы
                if not settings.get('board'):
                    error_msg = "Не указана доска для Pinterest"
                    print(error_msg)
                    results[f"pinterest_{account['id']}"] = {"success": False, "error": error_msg}
                    continue
                
                media_url = post_data.get('media', [None])[0] if post_data.get('media') else None
                if not media_url:
                    error_msg = "Pinterest требует медиафайл для публикации"
                    print(error_msg)
                    results[f"pinterest_{account['id']}"] = {"success": False, "error": error_msg}
                    continue
                
                print(f"Sending pin to Pinterest with title: {post_data['content'][:50]}...")
                result = pinterest_client.create_pin(
                    board_id=str(settings.get('board')),
                    title=post_data['content'][:100],  # Заголовок ограничен 100 символами
                    description=post_data['content'],
                    image_url=media_url
                )
                
                if 'error' in result:
                    print(f"Pinterest post failed: {result['error']}")
                    results[f"pinterest_{account['id']}"] = {"success": False, "error": result['error']}
                else:
                    print(f"Pinterest post successful: {result}")
                    results[f"pinterest_{account['id']}"] = {"success": True, "result": result}
                
            elif platform == 'youtube':
                youtube_client = YouTubeClient(access_token)
                
                media_path = post_data.get('media', [None])[0] if post_data.get('media') else None
                if not media_path:
                    error_msg = "YouTube требует медиафайл для публикации"
                    print(error_msg)
                    results[f"youtube_{account['id']}"] = {"success": False, "error": error_msg}
                    continue
                
                print(f"Uploading short to YouTube with title: {post_data['content'][:50]}...")
                result = youtube_client.upload_short(
                    video_path=media_path,
                    title=f"Тестовый пост: {post_data['content'][:50]}...",
                    description=post_data['content']
                )
                
                if 'error' in result:
                    print(f"YouTube upload failed: {result['error']}")
                    results[f"youtube_{account['id']}"] = {"success": False, "error": result['error']}
                else:
                    print(f"YouTube upload successful: {result}")
                    results[f"youtube_{account['id']}"] = {"success": True, "result": result}
                
        except Exception as e:
            import traceback
            platform = account.get('platform', 'unknown')
            error_message = str(e) if str(e) != "None" else "Неизвестная ошибка"
            print(f"Exception occurred while processing {platform} account {account['id']}: {error_message}")
            print(traceback.format_exc())
            results[f"{platform}_{account['id']}"] = {"success": False, "error": error_message}
    
    print(f"Completed send_test_post_to_all_platforms with results: {results}")
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