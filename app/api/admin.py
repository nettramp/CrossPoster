from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
import json

from app.models.social_account import SocialAccount as SocialAccountModel
from app.models.post import Post as PostModel
from app.models.statistics import Statistics as StatisticsModel
from app.schemas.social_account import SocialAccountCreate, SocialAccountPublic
from app.schemas.post import PostCreate, Post as PostSchema
from app.schemas.statistics import StatisticsCreate, Statistics as StatisticsSchema
from app.database import SessionLocal, engine
from app.core.config import settings
from app.social.vk_client import VKClient
from app.social.telegram_client import TelegramClient
from app.tasks.monitoring import repost_to_telegram, repost_to_vk, send_test_post_to_all_platforms

router = APIRouter(prefix="/admin", tags=["admin"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/accounts/status", response_model=List[dict])
async def get_connected_accounts_status(db=Depends(get_db)):
    """
    Получить статус подключения ко всем аккаунтам социальных сетей
    """
    accounts = db.query(SocialAccountModel).all()
    result = []
    
    for account in accounts:
        result.append({
            "id": account.id,
            "platform": account.platform,
            "account_name": account.account_name,
            "is_active": account.is_active,
            "connected_at": account.created_at.isoformat() if account.created_at else None
        })
    
    return result

@router.post("/posts/test")
async def send_test_post(
    content: str,
    media: Optional[List[str]] = None,
    db=Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    """
    Отправить тестовый пост во все подключенные социальные сети
    """
    try:
        # Получаем все активные аккаунты
        active_accounts = db.query(SocialAccountModel).filter(SocialAccountModel.is_active == True).all()
        
        if not active_accounts:
            raise HTTPException(status_code=400, detail="Нет подключенных аккаунтов")
        
        # Создаем тестовый пост
        test_post = Post(
            post_id=f"test_{datetime.utcnow().timestamp()}",
            content=content,
            media_urls=json.dumps(media) if media else None,
            posted_at=datetime.utcnow(),
            status="test",
            source_account_id=0  # тестовый пост
        )
        
        db.add(test_post)
        db.commit()
        db.refresh(test_post)
        
        # Подготовка данных аккаунтов для задачи
        accounts_data = []
        for account in active_accounts:
            accounts_data.append({
                "id": account.id,
                "platform": account.platform,
                "access_token": account.access_token,
                "username": account.account_name,
                "settings": account.settings or {}
            })
        
        # Подготовка данных поста
        post_data = {
            "content": content,
            "media": media
        }
        
        # Запуск задачи в фоне
        task_result = send_test_post_to_all_platforms.delay(post_data, accounts_data)
        
        # Сохраняем статистику
        stat = Statistics(
            date=datetime.utcnow().date(),
            posts_count=1,
            reposts_count=len(active_accounts),
            total_posts_made=1,
            account_id=active_accounts[0].id,  # используем первый аккаунт для статистики
        )
        db.add(stat)
        db.commit()
        
        return {
            "success": True,
            "message": f"Тестовый пост отправлен в {len(active_accounts)} аккаунтов",
            "task_id": task_result.id,
            "results": "Task queued for processing"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при отправке тестового поста: {str(e)}")

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
        # Проверяем, существует ли уже аккаунт для этой платформы у пользователя
        existing_account = db.query(SocialAccountModel).filter(
            SocialAccountModel.user_id == (account.user_id or 1),
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
                user_id=account.user_id or 1,  # по умолчанию первый пользователь
                settings=account.settings
            )
            db.add(db_account)
            db.commit()
            db.refresh(db_account)
            return db_account
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении аккаунта: {str(e)}")

@router.get("/social-accounts/status", response_model=List[SocialAccountPublic])
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
            "is_active": account.is_active
        })
    
    return result