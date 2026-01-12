import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://crossposter:crossposter@localhost:5432/crossposter"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Security
    secret_key: str = "crossposter_secret_key"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Social Media API Keys (default values, should be overridden by environment variables)
    vk_api_token: str = ""
    telegram_bot_token: str = ""
    instagram_username: str = ""
    instagram_password: str = ""
    pinterest_api_key: str = ""
    youtube_api_key: str = ""
    
    class Config:
        env_file = ".env"

settings = Settings()