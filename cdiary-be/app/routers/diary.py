from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import datetime
import uuid
import io
from PIL import Image

from app.database import get_db, AsyncSessionLocal
from app.models.models import User, Diary, DiaryChunk
from app.routers.jobs import create_job

from app.agent.worker import execute_job
from app.agent.models import DiaryEntryRequest

router = APIRouter()

# --- Models ---

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

# Constants for frontend request


# --- Helper Functions ---

async def process_pending_embeddings(user_id: str):
    """
    Background task to process pending diary chunk embeddings
    """
    from app.agent.bedrock import get_embedding
    from app.models.models import DiaryChunk, DiaryChunkEmbedding
    
    async with AsyncSessionLocal() as db:
        # Fetch chunks with pending status for this user
        uid = uuid.UUID(user_id) if isinstance(user_id, str) else user_id
        stmt = select(DiaryChunk).where(
            (DiaryChunk.user_id == uid) & 
            (DiaryChunk.embedding_status == 'pending')
        )
        result = await db.execute(stmt)
        chunks = result.scalars().all()
        
        if not chunks:
            return

        for chunk in chunks:
            try:
                # Generate embedding
                embedding_vector = get_embedding(chunk.content)
                
                if embedding_vector:
                    # Save to DiaryChunkEmbedding
                    db_embedding = DiaryChunkEmbedding(
                        chunk_id=chunk.id,
                        embedding_vector=embedding_vector
                    )
                    db.add(db_embedding)
                    
                    # Update chunk status
                    chunk.embedding_status = 'completed'
                    chunk.last_embedded_at = datetime.datetime.now(datetime.timezone.utc)
                else:
                    chunk.embedding_status = 'failed'
                    
            except Exception as e:
                print(f"DEBUG: Error processing embedding for chunk {chunk.id}: {e}", flush=True)
                chunk.embedding_status = 'failed'
                
        await db.commit()

# --- Endpoints ---

@router.post("/generate", response_model=Dict[str, str])
async def generate_diary_comic(
    request: DiaryEntryRequest, 
    background_tasks: BackgroundTasks,
    # user: User = Depends(get_current_user) # TODO: Add Auth
):
    import sys
    print(f"DEBUG: Received generation request for user...", flush=True)
    
    job_id = uuid.uuid4().hex
    create_job(job_id)

    # Fetch a fallback user ID if needed
    try:
        async with AsyncSessionLocal() as db:
            result = await db.execute(select(User))
            user = result.scalars().first()
            user_id = str(user.id) if user else "00000000-0000-0000-0000-000000000000"
            print(f"DEBUG: Using user_id {user_id}", flush=True)
    except Exception as e:
        print(f"DEBUG: Error fetching user: {e}", flush=True)
        user_id = "00000000-0000-0000-0000-000000000000"

    current_user_id = user_id # In production, get from token



    background_tasks.add_task(execute_job, job_id, current_user_id, request)
    
    return {"jobId": job_id}

@router.post("/", response_model=DiaryResponse)
async def create_diary(
    diary_in: DiaryCreate, 
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
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
    await db.flush() # Flush to get db_diary.id
    
    # Simple chunking logic: For now, create one chunk for the entire content
    # In a more advanced version, we would split by sentence or paragraph.
    db_chunk = DiaryChunk(
        diary_id=db_diary.id,
        user_id=uuid.UUID(diary_in.user_id),
        chunk_index=0,
        content=diary_in.content,
        embedding_status='pending'
    )
    db.add(db_chunk)
    
    await db.commit()
    await db.refresh(db_diary)
    
    # Trigger background task for embeddings
    background_tasks.add_task(process_pending_embeddings, diary_in.user_id)
    
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
