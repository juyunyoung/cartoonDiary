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

router = APIRouter()

class UserUpdate(BaseModel):
    name: Optional[str] = None
    profile_image_s3_key: Optional[str] = None
    profile_prompt: Optional[str] = None
    # Password update separate or here?

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
