from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.models.database import get_db
from app.models.post import Post as PostModel
from app.schemas.post import PostCreate, PostUpdate, Post as PostSchema

router = APIRouter(
    prefix="/posts",
    tags=["posts"]
)

@router.post("/", response_model=PostSchema)
def create_post(post: PostCreate, db: Session = Depends(get_db)):
    db_post = PostModel(
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

@router.get("/", response_model=List[PostSchema])
def read_posts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    posts = db.query(PostModel).offset(skip).limit(limit).all()
    return posts

@router.get("/{post_id}", response_model=PostSchema)
def read_post(post_id: int, db: Session = Depends(get_db)):
    db_post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return db_post

@router.put("/{post_id}", response_model=PostSchema)
def update_post(post_id: int, post: PostUpdate, db: Session = Depends(get_db)):
    db_post = db.query(PostModel).filter(PostModel.id == post_id).first()
    if db_post is None:
        raise HTTPException(status_code=404, detail="Post not found")

    update_data = post.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_post, key, value)

    db.commit()
    db.refresh(db_post)
    return db_post
