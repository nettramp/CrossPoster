from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class PostBase(BaseModel):
    post_id: str
    content: str
    media_urls: Optional[str] = None
    posted_at: datetime
    status: str

class PostCreate(PostBase):
    source_account_id: int

class PostUpdate(BaseModel):
    status: Optional[str] = None

class Post(PostBase):
    id: int
    source_account_id: int
    created_at: datetime

    class Config:
        orm_mode = True