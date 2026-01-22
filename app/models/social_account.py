from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.sql import func
from app.models.database import Base
from app.core.security import encrypt_data, decrypt_data

class SocialAccount(Base):
    __tablename__ = "social_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    platform = Column(String, index=True)  # vk, telegram, instagram, pinterest, youtube
    account_name = Column(String)
    _access_token = Column("access_token", String)
    settings = Column(JSON, nullable=True)
    _refresh_token = Column("refresh_token", String, nullable=True)
    
    @property
    def access_token(self):
        """Расшифровать токен при доступе"""
        if self._access_token:
            return decrypt_data(self._access_token)
        return None
    
    @access_token.setter
    def access_token(self, value):
        """Зашифровать токен при установке"""
        if value:
            self._access_token = encrypt_data(value)
    
    @property
    def refresh_token(self):
        """Расшифровать refresh токен при доступе"""
        if self._refresh_token:
            return decrypt_data(self._refresh_token)
        return None
    
    @refresh_token.setter
    def refresh_token(self, value):
        """Зашифровать refresh токен при установке"""
        if value:
            self._refresh_token = encrypt_data(value)
    token_expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())