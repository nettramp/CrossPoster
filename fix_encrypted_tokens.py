#!/usr/bin/env python3
"""
Скрипт для исправления зашифрованных токенов в базе данных.
Используется, когда токены были зашифрованы другим ключом шифрования.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.social_account import SocialAccount
from app.database import SessionLocal
from app.core.config import settings
from app.core.security import encrypt_data


def reset_encrypted_tokens():
    """
    Сброс зашифрованных токенов в базе данных.
    """
    print("Подключение к базе данных...")
    
    # Создаем сессию базы данных
    db = SessionLocal()
    
    try:
        # Получаем все аккаунты
        accounts = db.query(SocialAccount).all()
        
        print(f"Найдено {len(accounts)} аккаунтов для обновления")
        
        for account in accounts:
            print(f"Обновление аккаунта {account.id}: {account.platform} ({account.account_name})")
            
            # Очищаем зашифрованные токены (ставим пустую строку)
            account._access_token = ""
            account._refresh_token = ""
            
            # Обновляем аккаунт в базе данных
            db.add(account)
        
        # Сохраняем изменения
        db.commit()
        print("Все зашифрованные токены успешно сброшены.")
        print("\nТеперь вы можете ввести новые действительные токены через веб-интерфейс.")
        
    except Exception as e:
        print(f"Ошибка при сбросе токенов: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    reset_encrypted_tokens()