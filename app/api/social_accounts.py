from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models.database import get_db
from app.models.social_account import SocialAccount as SocialAccountModel
from app.schemas.social_account import SocialAccountCreate, SocialAccountUpdate, SocialAccountPublic

router = APIRouter(
    prefix="/social-accounts",
    tags=["social_accounts"]
)

@router.post("/", response_model=SocialAccountPublic)
def create_social_account(account: SocialAccountCreate, db: Session = Depends(get_db)):
    # Создаем экземпляр SQLAlchemy модели, а не Pydantic схемы
    db_account = SocialAccountModel(
        platform=account.platform,
        account_name=account.account_name,
        access_token=account.access_token,
        is_active=account.is_active,
        user_id=account.user_id or 1,  # по умолчанию первый пользователь
        settings=account.settings
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

@router.get("/", response_model=List[SocialAccountPublic])
def read_social_accounts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    accounts = db.query(SocialAccountModel).offset(skip).limit(limit).all()
    return accounts

@router.get("/{account_id}", response_model=SocialAccountPublic)
def read_social_account(account_id: int, db: Session = Depends(get_db)):
    db_account = db.query(SocialAccountModel).filter(SocialAccountModel.id == account_id).first()
    if db_account is None:
        raise HTTPException(status_code=404, detail="Social account not found")
    return db_account

@router.put("/{account_id}", response_model=SocialAccountPublic)
def update_social_account(account_id: int, account: SocialAccountUpdate, db: Session = Depends(get_db)):
    db_account = db.query(SocialAccountModel).filter(SocialAccountModel.id == account_id).first()
    if db_account is None:
        raise HTTPException(status_code=404, detail="Social account not found")
    
    for key, value in account.dict().items():
        if key != 'id':  # не обновляем ID
            setattr(db_account, key, value)
    
    db.commit()
    db.refresh(db_account)
    return db_account

@router.delete("/{account_id}")
def delete_social_account(account_id: int, db: Session = Depends(get_db)):
    db_account = db.query(SocialAccountModel).filter(SocialAccountModel.id == account_id).first()
    if db_account is None:
        raise HTTPException(status_code=404, detail="Social account not found")
    
    db.delete(db_account)
    db.commit()
    return {"message": "Social account deleted successfully"}