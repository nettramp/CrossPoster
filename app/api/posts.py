from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models.database import get_db
from app.models.post import Post
from app.schemas.post import PostCreate, Post

router = APIRouter(
    prefix="/posts",
    tags=["posts"]
)

@router.post("/", response_model=Post)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    db_post = Post(
        source_account_id=post.source_account_id,
        post_id=post.post_id,
        content=post.content,
        media_urls=post.media_urls,
        posted_at=post.posted_at,
        status=post.status
    )
    db.add(db_post)
    db.commit()
    db.refresh(db_post)
    return db_post

@router.get("/", response_model=List[Post])
def read_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    posts = db.query(Post).offset(skip).limit(limit).all()
    return posts

@router.get("/{post_id}", response_model=Post)
def read_post(post_id: int, db: Session = Depends(get_db)):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post

@router.put("/{post_id}", response_model=Post)
def update_post(post_id: int, post: PostCreate, db: Session = Depends(get_db)):
    db_post = db.query(Post).filter(Post.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    
    for key, value in post.dict().items():
        setattr(db_post, key, value)
    
    db.commit()
    db.refresh(db_post)
    return db_post

@router.post("/test")
def send_test_post(content: str, media: List[str] = None):
    """
    Отправить тестовый пост во все подключенные социальные сети
    """
    # Этот эндпоинт будет переопределен в админ-маршрутах
    # Здесь оставляем заглушку для совместимости
    return {"success": True, "message": "Test endpoint will be handled by admin router"}