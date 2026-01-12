from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models.database import get_db
from app.models.social_account import SocialAccount
from app.schemas.social_account import SocialAccountCreate, SocialAccount

router = APIRouter(
    prefix="/social-accounts",
    tags=["social_accounts"]
)

@router.post("/", response_model=SocialAccount)
def create_social_account(account: SocialAccountCreate, db: Session = Depends(get_db)):
    db_account = SocialAccount(
        platform=account.platform,
        account_name=account.account_name,
        access_token=account.access_token,
        is_active=account.is_active
    )
    db.add(db_account)
    db.commit()
    db.refresh(db_account)
    return db_account

@router.get("/", response_model=List[SocialAccount])
def read_social_accounts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    accounts = db.query(SocialAccount).offset(skip).limit(limit).all()
    return accounts

@router.get("/{account_id}", response_model=SocialAccount)
def read_social_account(account_id: int, db: Session = Depends(get_db)):
    db_account = db.query(SocialAccount).filter(SocialAccount.id == account_id).first()
    if db_account is None:
        raise HTTPException(status_code=404, detail="Social account not found")
    return db_account

@router.put("/{account_id}", response_model=SocialAccount)
def update_social_account(account_id: int, account: SocialAccountCreate, db: Session = Depends(get_db)):
    db_account = db.query(SocialAccount).filter(SocialAccount.id == account_id).first()
    if db_account is None:
        raise HTTPException(status_code=404, detail="Social account not found")
    
    for key, value in account.dict().items():
        setattr(db_account, key, value)
    
    db.commit()
    db.refresh(db_account)
    return db_account

@router.delete("/{account_id}")
def delete_social_account(account_id: int, db: Session = Depends(get_db)):
    db_account = db.query(SocialAccount).filter(SocialAccount.id == account_id).first()
    if db_account is None:
        raise HTTPException(status_code=404, detail="Social account not found")
    
    db.delete(db_account)
    db.commit()
    return {"message": "Social account deleted successfully"}