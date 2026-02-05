from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, Form
from fastapi.responses import JSONResponse
from typing import List, Optional
import asyncio
from datetime import datetime
import json
import os
import uuid
import shutil

from app.models.social_account import SocialAccount as SocialAccountModel
from app.models.post import Post as PostModel
from app.models.statistics import Statistics as StatisticsModel
from app.models.user import User as UserModel
from app.schemas.social_account import SocialAccountCreate, SocialAccountPublic
from app.schemas.post import PostCreate, Post as PostSchema
from app.schemas.statistics import StatisticsCreate, Statistics as StatisticsSchema
from app.database import SessionLocal, engine
from app.core.config import settings
from app.social.vk_client import VKClient
from app.social.telegram_client import TelegramClient
from app.social.instagram_client import InstagramClient
from app.social.pinterest_client import PinterestClient
from app.social.youtube_client import YouTubeClient
from app.tasks.monitoring import repost_to_telegram, repost_to_vk, send_test_post_to_all_platforms

router = APIRouter(prefix="/admin", tags=["admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_or_create_default_user(db):
    """Получить или создать пользователя по умолчанию"""
    user = db.query(UserModel).filter(UserModel.id == 1).first()
    if not user:
        user = UserModel(
            id=1,
            username="admin",
            email="admin@crossposter.local",
            password_hash="not_used"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

@router.post("/posts/test")
async def send_test_post(
    content: str = Form(...),
    target_platform: Optional[str] = Form(None),
    media: Optional[List[str]] = Form(None),
    db=Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Отправить тестовый пост во все подключенные социальные сети или в конкретную платформу
    """
    try:
        # Фильтруем аккаунты по выбранной платформе
        query = db.query(SocialAccountModel).filter(SocialAccountModel.is_active == True)
        if target_platform:
            query = query.filter(SocialAccountModel.platform == target_platform)
        
        active_accounts = query.all()
        
        if not active_accounts:
            platform_msg = f"платформу {target_platform}" if target_platform else "подключенные аккаунты"
            raise HTTPException(status_code=400, detail=f"Нет активных аккаунтов для {platform_msg}")
        
        # Создаем тестовый пост
        test_post = PostModel(
            post_id=f"test_{datetime.utcnow().timestamp()}",
            content=content,
            media_urls=json.dumps(media) if media else None,
            posted_at=datetime.utcnow(),
            status="test",
            source_account_id=active_accounts[0].id  # используем ID первого активного аккаунта
        )
        
        db.add(test_post)
        db.commit()
        db.refresh(test_post)
        
        # Подготовка данных аккаунтов для задачи
        accounts_data = []
        for account in active_accounts:
            try:
                access_token = account.access_token
                print(f"Successfully decrypted access token for account {account.id} ({account.platform})")
            except Exception as e:
                # Если токен не может быть расшифрован, пропускаем этот аккаунт
                print(f"Error decrypting access token for account {account.id} ({account.platform}): {str(e)}")
                continue
            
            accounts_data.append({
                "id": account.id,
                "platform": account.platform,
                "access_token": access_token,
                "username": account.account_name,
                "settings": account.settings or {}
            })
        
        # Подготовка данных поста
        post_data = {
            "content": content,
            "media": media
        }
        
        # Вызов задачи через Celery
        task_result = send_test_post_to_all_platforms.delay(post_data, accounts_data)
        
        # Логирование для отладки
        print(f"Task sent to Celery: {task_result.id}")
        
        # Сохраняем статистику
        stat = StatisticsModel(
            date=datetime.utcnow().date(),
            posts_count=1,
            reposts_count=len(active_accounts),
            total_posts_made=1,
            account_id=active_accounts[0].id,  # используем первый аккаунт для статистики
        )
        db.add(stat)
        db.commit()
        
        platform_msg = f"в {target_platform}" if target_platform else "во все подключенные социальные сети"
        return {
            "success": True,
            "message": f"Тестовый пост отправлен {platform_msg} ({len(active_accounts)} аккаунт(ов))",
            "task_id": "async_task_added",
            "results": f"Test post queued for {len(active_accounts)} account(s)"
        }
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Ошибка при отправке тестового поста: {str(e)}")
        print(f"Трейс ошибки: {error_details}")
        error_message = str(e) if str(e) != "None" else "Неизвестная ошибка"
        raise HTTPException(status_code=500, detail=f"Ошибка при отправке тестового поста: {error_message}\nДетали: {error_details}")

@router.post("/posts/crosspost")
async def crosspost_posts(
    request: dict,
    db=Depends(get_db)
):
    """
    Выполнить кросс-постинг из одной социальной сети в другую
    """
    try:
        source_platform = request.get('source_platform')
        target_platform = request.get('target_platform')
        posts_count = request.get('posts_count', 1)
        
        if not source_platform:
            raise HTTPException(status_code=400, detail="Не указан источник (source_platform)")
        
        if not target_platform:
            raise HTTPException(status_code=400, detail="Не указан получатель (target_platform)")
        
        if not isinstance(posts_count, int) or posts_count < 1:
            raise HTTPException(status_code=400, detail="Количество постов должно быть положительным числом")
        
        # Получаем активные аккаунты для источника и цели
        source_accounts = db.query(SocialAccountModel).filter(
            SocialAccountModel.platform == source_platform,
            SocialAccountModel.is_active == True
        ).all()
        
        target_accounts = db.query(SocialAccountModel).filter(
            SocialAccountModel.platform == target_platform,
            SocialAccountModel.is_active == True
        ).all()
        
        if not source_accounts:
            raise HTTPException(status_code=400, detail=f"Нет активных аккаунтов для источника: {source_platform}")
        
        if not target_accounts:
            raise HTTPException(status_code=400, detail=f"Нет активных аккаунтов для цели: {target_platform}")
        
        # Выбираем первый активный аккаунт из каждой платформы
        source_account = source_accounts[0]
        target_account = target_accounts[0]
        
        # Получаем последние посты из источника
        posts_to_repost = []
        
        # Используем соответствующий клиент для получения постов из источника
        if source_platform == 'vk':
            vk_client = VKClient(source_account.access_token)
            # Получаем последние посты из VK
            posts = vk_client.get_latest_posts(str(source_account.settings.get('owner_id', '')), count=posts_count)
            for post in posts:
                post_content = post.get('text', '')
                post_media = []
                
                if 'attachments' in post:
                    for attachment in post['attachments']:
                        if attachment['type'] == 'photo':
                            sizes = attachment['photo']['sizes']
                            max_size_photo = max(sizes, key=lambda x: x['width'])
                            post_media.append(max_size_photo['url'])
                
                posts_to_repost.append({
                    'content': post_content,
                    'media': post_media
                })
                
        elif source_platform == 'telegram':
            telegram_client = TelegramClient(source_account.access_token)
            
            # Асинхронный вызов в синхронной функции
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            posts = loop.run_until_complete(
                telegram_client.get_latest_posts(str(source_account.settings.get('chat_id', '')), limit=posts_count)
            )
            loop.close()
            
            for post in posts:
                post_content = post.get('text', '')
                post_media = [post.get('media_url')] if post.get('media_url') else []
                
                posts_to_repost.append({
                    'content': post_content,
                    'media': post_media
                })
                
        elif source_platform == 'instagram':
            instagram_client = InstagramClient(
                username=source_account.access_token.split(':')[0],
                password=source_account.access_token.split(':')[1]
            )
            posts = instagram_client.get_latest_posts(
                user_id=str(source_account.settings.get('user_id', '')),
                count=posts_count
            )
            for post in posts:
                post_content = post.get('caption', '')
                post_media = [post.get('media_url')] if post.get('media_url') else []
                
                posts_to_repost.append({
                    'content': post_content,
                    'media': post_media
                })
                
        elif source_platform == 'pinterest':
            pinterest_client = PinterestClient(source_account.access_token)
            posts = pinterest_client.get_latest_pins(
                board_id=str(source_account.settings.get('board_id', '')),
                count=posts_count
            )
            for post in posts:
                post_content = post.get('description', '')
                post_media = [post.get('image_url')] if post.get('image_url') else []
                
                posts_to_repost.append({
                    'content': post_content,
                    'media': post_media
                })
                
        elif source_platform == 'youtube':
            youtube_client = YouTubeClient(source_account.access_token)
            posts = youtube_client.get_latest_videos(
                channel_id=str(source_account.settings.get('channel_id', '')),
                count=posts_count
            )
            for post in posts:
                post_content = post.get('title', '') + '\n' + post.get('description', '')
                post_media = [post.get('thumbnail_url')] if post.get('thumbnail_url') else []
                
                posts_to_repost.append({
                    'content': post_content,
                    'media': post_media
                })

        # Отправляем каждый пост в целевую платформу
        results = []
        for i, post_data in enumerate(posts_to_repost[:posts_count]):
            if target_platform == 'vk':
                vk_client = VKClient(target_account.access_token)
                
                # Обработка медиафайлов для VK
                attachments = []
                if post_data.get('media'):
                    for media_url in post_data['media']:
                        # Скачиваем и загружаем медиа в VK
                        from app.utils.media_downloader import download_media, get_file_extension
                        file_extension = get_file_extension(media_url)
                        temp_filename = f"/tmp/{uuid.uuid4()}.{file_extension}"
                        
                        downloaded_path = download_media(media_url, temp_filename)
                        if downloaded_path:
                            # Загружаем в VK
                            attachment = vk_client.upload_photo(downloaded_path, str(target_account.settings.get('group_id', '')))
                            if attachment:
                                attachments.append(attachment)
                
                result = vk_client.post_to_wall(
                    owner_id=str(target_account.settings.get('group_id', '')),
                    message=post_data['content'],
                    attachments=attachments
                )
                results.append(result)
                
            elif target_platform == 'telegram':
                telegram_client = TelegramClient(target_account.access_token)
                
                # Асинхронный вызов в синхронной функции
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(
                    telegram_client.post_to_channel(
                        chat_id=str(target_account.settings.get('channel', '')),
                        text=post_data['content'],
                        media=post_data.get('media', [])
                    )
                )
                loop.close()
                results.append(result)
                
            elif target_platform == 'instagram':
                # Для Instagram нужно использовать учетные данные
                credentials = target_account.access_token.split(':')
                if len(credentials) >= 2:
                    instagram_client = InstagramClient(
                        username=credentials[0],
                        password=credentials[1]
                    )
                    
                    # Instagram требует медиафайл для публикации
                    if post_data.get('media'):
                        media_url = post_data['media'][0]  # берем первое медиа
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
                        results.append(result)
                    else:
                        # Без медиа нельзя опубликовать в Instagram
                        results.append({'error': 'Instagram requires media file for posting'})
            
            elif target_platform == 'pinterest':
                pinterest_client = PinterestClient(target_account.access_token)
                
                if post_data.get('media'):
                    media_url = post_data['media'][0]  # берем первое медиа
                    result = pinterest_client.create_pin(
                        board_id=str(target_account.settings.get('board_id', '')),
                        title=post_data['content'][:100],  # Заголовок ограничен 100 символами
                        description=post_data['content'],
                        image_url=media_url
                    )
                    results.append(result)
                else:
                    results.append({'error': 'Pinterest requires media file for posting'})
                
            elif target_platform == 'youtube':
                youtube_client = YouTubeClient(target_account.access_token)
                
                if post_data.get('media'):
                    media_path = post_data['media'][0]  # берем первое медиа
                    result = youtube_client.upload_short(
                        video_path=media_path,
                        title=f"Репост: {post_data['content'][:50]}...",
                        description=post_data['content']
                    )
                    results.append(result)
                else:
                    results.append({'error': 'YouTube requires media file for posting'})
        
        # Сохраняем статистику
        stat = StatisticsModel(
            date=datetime.utcnow().date(),
            posts_count=len(results),
            reposts_count=len(results),
            total_posts_made=len(results),
            account_id=target_account.id,
        )
        db.add(stat)
        db.commit()
        
        return {
            "success": True,
            "message": f"Успешно выполнено {len(results)} репостов из {source_platform} в {target_platform}",
            "results": results
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Ошибка при выполнении кросс-постинга: {str(e)}")
        print(f"Трейс ошибки: {error_details}")
        error_message = str(e) if str(e) != "None" else "Неизвестная ошибка"
        raise HTTPException(status_code=500, detail=f"Ошибка при выполнении кросс-постинга: {error_message}\nДетали: {error_details}")

@router.get("/posts/preview")
async def preview_posts(
   source_platform: str,
   limit: int = 5,
   db=Depends(get_db)
):
   """
   Предварительный просмотр постов из источника без их репоста
   """
   try:
       if not source_platform:
           raise HTTPException(status_code=400, detail="Не указан источник (source_platform)")
       
       if limit < 1 or limit > 20:
           raise HTTPException(status_code=400, detail="Лимит должен быть от 1 до 20")
       
       # Получаем активные аккаунты для источника
       source_accounts = db.query(SocialAccountModel).filter(
           SocialAccountModel.platform == source_platform,
           SocialAccountModel.is_active == True
       ).all()
       
       if not source_accounts:
           raise HTTPException(status_code=400, detail=f"Нет активных аккаунтов для источника: {source_platform}")
       
       # Выбираем первый активный аккаунт
       source_account = source_accounts[0]
       
       # Получаем последние посты из источника
       posts_preview = []
       
       # Используем соответствующий клиент для получения постов из источника
       if source_platform == 'vk':
           vk_client = VKClient(source_account.access_token)
           # Получаем последние посты из VK
           posts = vk_client.get_latest_posts(str(source_account.settings.get('owner_id', '')), count=limit)
           for post in posts:
               post_content = post.get('text', '')
               post_media = []
               
               if 'attachments' in post:
                   for attachment in post['attachments']:
                       if attachment['type'] == 'photo':
                           sizes = attachment['photo']['sizes']
                           max_size_photo = max(sizes, key=lambda x: x['width'])
                           post_media.append(max_size_photo['url'])
               
               posts_preview.append({
                   'content': post_content,
                   'media': post_media
               })
               
       elif source_platform == 'telegram':
           telegram_client = TelegramClient(source_account.access_token)
           
           # Асинхронный вызов в синхронной функции
           loop = asyncio.new_event_loop()
           asyncio.set_event_loop(loop)
           posts = loop.run_until_complete(
               telegram_client.get_latest_posts(str(source_account.settings.get('chat_id', '')), limit=limit)
           )
           loop.close()
           
           for post in posts:
               post_content = post.get('text', '')
               post_media = [post.get('media_url')] if post.get('media_url') else []
               
               posts_preview.append({
                   'content': post_content,
                   'media': post_media
               })
               
       elif source_platform == 'instagram':
           instagram_client = InstagramClient(
               username=source_account.access_token.split(':')[0],
               password=source_account.access_token.split(':')[1]
           )
           posts = instagram_client.get_latest_posts(
               user_id=str(source_account.settings.get('user_id', '')),
               count=limit
           )
           for post in posts:
               post_content = post.get('caption', '')
               post_media = [post.get('media_url')] if post.get('media_url') else []
               
               posts_preview.append({
                   'content': post_content,
                   'media': post_media
               })
               
       elif source_platform == 'pinterest':
           pinterest_client = PinterestClient(source_account.access_token)
           posts = pinterest_client.get_latest_pins(
               board_id=str(source_account.settings.get('board_id', '')),
               count=limit
           )
           for post in posts:
               post_content = post.get('description', '')
               post_media = [post.get('image_url')] if post.get('image_url') else []
               
               posts_preview.append({
                   'content': post_content,
                   'media': post_media
               })
               
       elif source_platform == 'youtube':
           youtube_client = YouTubeClient(source_account.access_token)
           posts = youtube_client.get_latest_videos(
               channel_id=str(source_account.settings.get('channel_id', '')),
               count=limit
           )
           for post in posts:
               post_content = post.get('title', '') + '\n' + post.get('description', '')
               post_media = [post.get('thumbnail_url')] if post.get('thumbnail_url') else []
               
               posts_preview.append({
                   'content': post_content,
                   'media': post_media
               })

       return {
           "success": True,
           "posts": posts_preview
       }
       
   except Exception as e:
       import traceback
       error_details = traceback.format_exc()
       print(f"Ошибка при получении превью постов: {str(e)}")
       print(f"Трейс ошибки: {error_details}")
       error_message = str(e) if str(e) != "None" else "Неизвестная ошибка"
       raise HTTPException(status_code=500, detail=f"Ошибка при получении превью постов: {error_message}\nДетали: {error_details}")

@router.post("/upload-media")
async def upload_media_endpoint(files: List[UploadFile] = Form(None)):
    """
    Загрузить медиафайлы и получить их URL-адреса
    """
    try:
        if not files:
            return {"urls": []}
        
        urls = []
        
        # Создаем директорию для хранения загруженных файлов, если её нет
        media_dir = "app/static/media"
        os.makedirs(media_dir, exist_ok=True)
        
        for file in files:
            # Генерируем уникальное имя файла
            file_ext = file.filename.split(".")[-1]
            unique_filename = f"{uuid.uuid4()}.{file_ext}"
            file_path = os.path.join(media_dir, unique_filename)
            
            # Сохраняем файл
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Формируем URL (относительно static директории)
            file_url = f"/static/media/{unique_filename}"
            urls.append(file_url)
        
        return {"urls": urls}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при загрузке медиа: {str(e)}")

@router.get("/statistics/summary")
async def get_summary_statistics(db=Depends(get_db)):
    """
    Получить сводную статистику
    """
    total_posts = db.query(PostModel).count()
    active_accounts = db.query(SocialAccountModel).filter(SocialAccountModel.is_active == True).count()
    
    # Получаем последнюю запись статистики
    last_stat = db.query(StatisticsModel).order_by(StatisticsModel.created_at.desc()).first()
    
    return {
        "total_posts": total_posts,
        "reposts_count": total_posts,  # приближенное значение
        "active_accounts": active_accounts,
        "last_sync": last_stat.created_at.isoformat() if last_stat else "-"
    }

@router.post("/social-accounts/", response_model=SocialAccountPublic)
async def create_or_update_social_account(account: SocialAccountCreate, db=Depends(get_db)):
    """
    Создать или обновить аккаунт социальной сети
    """
    try:
        # Убеждаемся, что пользователь по умолчанию существует
        user_id = account.user_id or 1
        get_or_create_default_user(db)
        
        # Проверяем, существует ли уже аккаунт для этой платформы у пользователя
        existing_account = db.query(SocialAccountModel).filter(
            SocialAccountModel.user_id == user_id,
            SocialAccountModel.platform == account.platform
        ).first()
        
        if existing_account:
            # Обновляем существующий аккаунт
            existing_account.account_name = account.account_name
            existing_account.access_token = account.access_token  # будет зашифрован автоматически через модель
            existing_account.is_active = account.is_active
            existing_account.settings = account.settings
            db.commit()
            db.refresh(existing_account)
            return existing_account
        else:
            # Создаем новый аккаунт
            db_account = SocialAccountModel(
                platform=account.platform,
                account_name=account.account_name,
                access_token=account.access_token,  # будет зашифрован автоматически через модель
                is_active=account.is_active or True,
                user_id=user_id,
                settings=account.settings
            )
            db.add(db_account)
            db.commit()
            db.refresh(db_account)
            return db_account
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении аккаунта: {str(e)}")

@router.get("/social-accounts/status")
async def get_all_accounts_status(db=Depends(get_db)):
    """
    Получить статус всех аккаунтов
    """
    accounts = db.query(SocialAccountModel).all()
    result = []
    
    for account in accounts:
        result.append({
            "id": account.id,
            "platform": account.platform,
            "account_name": account.account_name,
            "is_active": account.is_active,
            "created_at": account.created_at.isoformat() if account.created_at else None
        })
    
    return result


@router.get("/social-accounts/detailed")
async def get_detailed_accounts_status(db=Depends(get_db)):
    """
    Получить детальную информацию о всех аккаунтах с статистикой репостов
    """
    from sqlalchemy import func as sql_func
    
    accounts = db.query(SocialAccountModel).all()
    
    # Группируем аккаунты по платформам
    platforms = {}
    
    for account in accounts:
        platform = account.platform.lower()
        
        # Получаем статистику репостов для этого аккаунта
        stats = db.query(
            sql_func.coalesce(sql_func.sum(StatisticsModel.reposts_count), 0).label('total_reposts'),
            sql_func.coalesce(sql_func.sum(StatisticsModel.posts_count), 0).label('total_posts')
        ).filter(StatisticsModel.account_id == account.id).first()
        
        # Получаем количество тестовых постов
        test_posts_count = db.query(PostModel).filter(
            PostModel.status == "test"
        ).count()
        
        account_data = {
            "id": account.id,
            "account_name": account.account_name,
            "is_active": account.is_active,
            "created_at": account.created_at.isoformat() if account.created_at else None,
            "updated_at": account.updated_at.isoformat() if account.updated_at else None,
            "settings": account.settings or {},
            "reposts_count": int(stats.total_reposts) if stats else 0,
            "posts_count": int(stats.total_posts) if stats else 0,
            "test_posts_count": test_posts_count
        }
        
        if platform not in platforms:
            platforms[platform] = {
                "platform": platform,
                "accounts": [],
                "total_accounts": 0,
                "active_accounts": 0,
                "total_reposts": 0,
                "total_test_posts": 0
            }
        
        platforms[platform]["accounts"].append(account_data)
        platforms[platform]["total_accounts"] += 1
        if account.is_active:
            platforms[platform]["active_accounts"] += 1
        platforms[platform]["total_reposts"] += account_data["reposts_count"]
        platforms[platform]["total_test_posts"] += account_data["test_posts_count"]
    
    return {
        "platforms": platforms,
        "summary": {
            "total_accounts": len(accounts),
            "active_accounts": sum(1 for a in accounts if a.is_active),
            "platforms_count": len(platforms)
        }
    }


@router.get("/social-accounts/{account_id}")
async def get_account_details(account_id: int, db=Depends(get_db)):
    """
    Получить детальную информацию об аккаунте
    """
    from sqlalchemy import func as sql_func
    
    account = db.query(SocialAccountModel).filter(SocialAccountModel.id == account_id).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    
    # Получаем статистику репостов для этого аккаунта
    stats = db.query(
        sql_func.coalesce(sql_func.sum(StatisticsModel.reposts_count), 0).label('total_reposts'),
        sql_func.coalesce(sql_func.sum(StatisticsModel.posts_count), 0).label('total_posts')
    ).filter(StatisticsModel.account_id == account.id).first()
    
    return {
        "id": account.id,
        "platform": account.platform,
        "account_name": account.account_name,
        "is_active": account.is_active,
        "created_at": account.created_at.isoformat() if account.created_at else None,
        "updated_at": account.updated_at.isoformat() if account.updated_at else None,
        "settings": account.settings or {},
        "reposts_count": int(stats.total_reposts) if stats else 0,
        "posts_count": int(stats.total_posts) if stats else 0
    }


@router.put("/social-accounts/{account_id}")
async def update_account(account_id: int, account: SocialAccountCreate, db=Depends(get_db)):
    """
    Обновить аккаунт социальной сети
    """
    existing_account = db.query(SocialAccountModel).filter(SocialAccountModel.id == account_id).first()
    
    if not existing_account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    
    try:
        existing_account.account_name = account.account_name
        if account.access_token:
            existing_account.access_token = account.access_token
        existing_account.is_active = account.is_active
        existing_account.settings = account.settings
        
        db.commit()
        db.refresh(existing_account)
        
        return {
            "id": existing_account.id,
            "platform": existing_account.platform,
            "account_name": existing_account.account_name,
            "is_active": existing_account.is_active,
            "settings": existing_account.settings
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при обновлении аккаунта: {str(e)}")


@router.delete("/social-accounts/{account_id}")
async def delete_account(account_id: int, db=Depends(get_db)):
    """
    Удалить аккаунт социальной сети
    """
    account = db.query(SocialAccountModel).filter(SocialAccountModel.id == account_id).first()
    
    if not account:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    
    try:
        db.delete(account)
        db.commit()
        return {"success": True, "message": "Аккаунт успешно удален"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка при удалении аккаунта: {str(e)}")
