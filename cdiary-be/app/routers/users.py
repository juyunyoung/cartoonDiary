from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import Optional
import uuid

from app.database import get_db
from app.models.models import User
from app.auth.security import get_password_hash # If password update needed

# Basic dependency to get current user from token would be better, 
# for now we'll accept userId in path/body for MVP simplicity as per user request to "add/delete/update"

from app.agent.bedrock import make_access_url, S3_BUCKET

router = APIRouter()

class UserUpdate(BaseModel):
    name: Optional[str] = None
    profile_image_s3_key: Optional[str] = None
    profile_prompt: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    profile_image_url: Optional[str] = None
    status: str

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    url = None
    if user.profile_image_s3_key:
        url = make_access_url(S3_BUCKET, user.profile_image_s3_key)
        
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "profile_image_url": url,
        "status": user.status
    }

@router.put("/{user_id}")
async def update_user(user_id: str, user_data: UserUpdate, db: AsyncSession = Depends(get_db)):
    # Convert string uuid to UUID object for query if needed, or SQLAlchemy handles it via TypeDecorator
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    if user_data.name is not None:
        user.name = user_data.name
    if user_data.profile_image_s3_key is not None:
        user.profile_image_s3_key = user_data.profile_image_s3_key
    if user_data.profile_prompt is not None:
        user.profile_prompt = user_data.profile_prompt
        
    await db.commit()
    await db.refresh(user)
    
    return {
        "status": "success",
        "user_id": str(user.id),
        "username": user.username,
        "profile_image_s3_key": user.profile_image_s3_key
    }

@router.delete("/{user_id}")
async def delete_user(user_id: str, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    await db.delete(user)
    await db.commit()
    
    return {"status": "success", "message": "User deleted"}
