from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models.database import get_db
from app.models.user import User as UserModel
from app.schemas.user import UserCreate, User as UserSchema
from app.core.security import hash_password

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

@router.post("/", response_model=UserSchema)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    password_hash = hash_password(user.password)
    db_user = UserModel(username=user.username, email=user.email, password_hash=password_hash)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/", response_model=List[UserSchema])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(UserModel).offset(skip).limit(limit).all()
    return users

@router.get("/{user_id}", response_model=UserSchema)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user
