from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class SocialAccountBase(BaseModel):
    platform: str
    account_name: str
    is_active: bool = True

class SocialAccountCreate(SocialAccountBase):
    access_token: str
    user_id: int = 1  # по умолчанию первый пользователь
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    settings: Optional[dict] = None

class SocialAccountUpdate(SocialAccountBase):
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    token_expires_at: Optional[datetime] = None
    settings: Optional[dict] = None

class SocialAccountPublic(SocialAccountBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    settings: Optional[dict] = None

    class Config:
        orm_mode = True
        schema_extra = {
            "example": {
                "id": 1,
                "user_id": 1,
                "platform": "vk",
                "account_name": "My VK Account",
                "is_active": True,
                "created_at": "2023-01-01T00:00:00",
                "updated_at": "2023-01-01T00:00:00",
                "settings": {}
            }
        }


class SocialAccount(SocialAccountCreate):
    id: int
    user_id: int
    created_at: datetime
    updated_at: Optional[datetime]
    settings: Optional[dict] = None

    class Config:
        orm_mode = True