from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.models.database import get_db
from app.models.statistics import Statistics
from app.schemas.statistics import StatisticsCreate, Statistics

router = APIRouter(
    prefix="/statistics",
    tags=["statistics"]
)

@router.post("/", response_model=Statistics)
def create_statistics(stat: StatisticsCreate, db: Session = Depends(get_db)):
    db_stat = Statistics(
        account_id=stat.account_id,
        date=stat.date,
        posts_count=stat.posts_count,
        reposts_count=stat.reposts_count,
        total_posts_made=stat.total_posts_made,
        time_spent_seconds=stat.time_spent_seconds
    )
    db.add(db_stat)
    db.commit()
    db.refresh(db_stat)
    return db_stat

@router.get("/", response_model=List[Statistics])
def read_statistics(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    stats = db.query(Statistics).offset(skip).limit(limit).all()
    return stats

@router.get("/{stat_id}", response_model=Statistics)
def read_statistics(stat_id: int, db: Session = Depends(get_db)):
    db_stat = db.query(Statistics).filter(Statistics.id == stat_id).first()
    if db_stat is None:
        raise HTTPException(status_code=404, detail="Statistics not found")
    return db_stat

@router.get("/account/{account_id}", response_model=List[Statistics])
def read_account_statistics(account_id: int, db: Session = Depends(get_db)):
    stats = db.query(Statistics).filter(Statistics.account_id == account_id).all()
    return stats