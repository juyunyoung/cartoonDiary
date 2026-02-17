from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional, List
import datetime
import uuid

from app.database import get_db
from app.models.models import User, Diary

router = APIRouter()

class DiaryCreate(BaseModel):
    user_id: str
    diary_date: datetime.date
    content: str
    image_s3_key: Optional[str] = None
    
class DiaryUpdate(BaseModel):
    content: Optional[str] = None
    image_s3_key: Optional[str] = None

class DiaryResponse(BaseModel):
    id: str
    diary_date: datetime.date
    content: str
    image_s3_key: Optional[str] = None
    created_at: datetime.datetime

@router.post("/", response_model=DiaryResponse)
async def create_diary(diary_in: DiaryCreate, db: AsyncSession = Depends(get_db)):
    # Check if duplicate for date
    stmt = select(Diary).where((Diary.user_id == diary_in.user_id) & (Diary.diary_date == diary_in.diary_date))
    result = await db.execute(stmt)
    existing = result.scalars().first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Diary already exists for this date")
        
    db_diary = Diary(
        user_id=diary_in.user_id,
        diary_date=diary_in.diary_date,
        content=diary_in.content,
        image_s3_key=diary_in.image_s3_key
    )
    db.add(db_diary)
    await db.commit()
    await db.refresh(db_diary)
    
    return {
        "id": str(db_diary.id), # Convert UUID
        "diary_date": db_diary.diary_date,
        "content": db_diary.content,
        "image_s3_key": db_diary.image_s3_key,
        "created_at": db_diary.created_at
    }

@router.get("/user/{user_id}", response_model=List[DiaryResponse])
async def get_user_diaries(user_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Diary).where(Diary.user_id == user_id).order_by(Diary.diary_date.desc())
    result = await db.execute(stmt)
    diaries = result.scalars().all()
    
    return [
        {
            "id": str(d.id),
            "diary_date": d.diary_date,
            "content": d.content,
            "image_s3_key": d.image_s3_key,
            "created_at": d.created_at
        }
        for d in diaries
    ]

@router.get("/search", response_model=List[DiaryResponse])
async def search_diaries(user_id: str, query: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Diary).where(
        (Diary.user_id == user_id) & 
        (Diary.content.contains(query))
    ).order_by(Diary.diary_date.desc())
    
    result = await db.execute(stmt)
    diaries = result.scalars().all()
    
    return [
        {
            "id": str(d.id),
            "diary_date": d.diary_date,
            "content": d.content,
            "image_s3_key": d.image_s3_key,
            "created_at": d.created_at
        }
        for d in diaries
    ]

@router.get("/{diary_id}", response_model=DiaryResponse)
async def get_diary(diary_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Diary).where(Diary.id == diary_id)
    result = await db.execute(stmt)
    diary = result.scalars().first()
    
    if not diary:
        raise HTTPException(status_code=404, detail="Diary not found")
        
    return {
        "id": str(diary.id),
        "diary_date": diary.diary_date,
        "content": diary.content,
        "image_s3_key": diary.image_s3_key,
        "created_at": diary.created_at
    }

@router.delete("/{diary_id}")
async def delete_diary(diary_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Diary).where(Diary.id == diary_id)
    result = await db.execute(stmt)
    diary = result.scalars().first()
    
    if not diary:
        raise HTTPException(status_code=404, detail="Diary not found")
        
    await db.delete(diary)
    await db.commit()
    
    return {"status": "success", "message": "Diary deleted"}
