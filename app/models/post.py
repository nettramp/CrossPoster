from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.database import Base

class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, index=True)
    source_account_id = Column(Integer, ForeignKey("social_accounts.id"))
    post_id = Column(String)  # ID поста в оригинальной соцсети
    content = Column(String)  # Текст поста
    media_urls = Column(String)  # Ссылки на медиафайлы (через запятую)
    posted_at = Column(DateTime)  # Время публикации в оригинальной соцсети
    status = Column(String)  # pending, posted, failed
    created_at = Column(DateTime(timezone=True), server_default=func.now())