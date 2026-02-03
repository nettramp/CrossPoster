from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import datetime
import json

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
    content: str,
    target_platform: Optional[str] = None,
    media: Optional[List[str]] = None,
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
