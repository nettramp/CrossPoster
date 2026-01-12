from sqlalchemy import Column, Integer, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.models.database import Base

class Statistics(Base):
    __tablename__ = "statistics"

    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(Integer, ForeignKey("social_accounts.id"))
    date = Column(Date)  # Дата статистики
    posts_count = Column(Integer, default=0)  # Количество оригинальных постов
    reposts_count = Column(Integer, default=0)  # Количество репостов
    total_posts_made = Column(Integer, default=0)  # Общее количество сделанных постов
    time_spent_seconds = Column(Integer, default=0)  # Время, затраченное на постинг (в секундах)
    created_at = Column(DateTime(timezone=True), server_default=func.now())