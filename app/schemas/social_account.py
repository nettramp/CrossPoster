from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class SocialAccountBase(BaseModel):
    platform: str
    account_name: str
    is_active: bool = True

class SocialAccountCreate(SocialAccountBase):
    access_token: str
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    settings: Optional[dict] = None

class SocialAccountUpdate(SocialAccountBase):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    settings: Optional[dict] = None

class SocialAccount(SocialAccountBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    settings: Optional[dict] = None

    class Config:
        orm_mode = True