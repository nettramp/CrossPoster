from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class StatisticsBase(BaseModel):
    date: date
    posts_count: int = 0
    reposts_count: int = 0
    total_posts_made: int = 0
    time_spent_seconds: int = 0

class StatisticsCreate(StatisticsBase):
    account_id: int

class StatisticsUpdate(BaseModel):
    posts_count: Optional[int] = None
    reposts_count: Optional[int] = None
    total_posts_made: Optional[int] = None
    time_spent_seconds: Optional[int] = None

class Statistics(StatisticsBase):
    id: int
    account_id: int
    created_at: datetime

    class Config:
        orm_mode = True