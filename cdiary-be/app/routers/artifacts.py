from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import datetime

from app.database import get_db
from app.models.models import Diary, DiaryChunk
from app.agent.bedrock import make_access_url, S3_BUCKET

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])

class Panel(BaseModel):
    text: str

class Storyboard(BaseModel):
    panels: List[Panel]

class ArtifactResponse(BaseModel):
    artifactId: str
    finalStripUrl: str
    panelUrls: List[str]
    storyboard: Storyboard
    stylePreset: str
    createdAt: datetime.datetime

@router.get("/", response_model=Dict[str, List[Any]])
async def list_artifacts(limit: int = 20, db: AsyncSession = Depends(get_db)):
    # Simple list of recent diaries
    stmt = select(Diary).order_by(Diary.created_at.desc()).limit(limit)
    result = await db.execute(stmt)
    diaries = result.scalars().all()
    
    items = []
    for d in diaries:
        url = ""
        if d.image_s3_key:
             url = make_access_url(S3_BUCKET, d.image_s3_key)
             
        items.append({
            "artifactId": str(d.id),
            "thumbnailUrl": url,
            "date": str(d.diary_date),
            "summary": d.content[:50] + "...",
            "stylePreset": "comic"
        })
        
    return {"items": items}

@router.get("/{artifact_id}", response_model=ArtifactResponse)
async def get_artifact(artifact_id: str, db: AsyncSession = Depends(get_db)):
    # 1. Fetch Diary
    stmt = select(Diary).where(Diary.id == artifact_id)
    result = await db.execute(stmt)
    diary = result.scalars().first()
    
    if not diary:
        raise HTTPException(status_code=404, detail="Artifact not found")
        
    # 2. Fetch Chunks
    stmt_chunks = select(DiaryChunk).where(DiaryChunk.diary_id == artifact_id).order_by(DiaryChunk.chunk_index)
    result_chunks = await db.execute(stmt_chunks)
    chunks = result_chunks.scalars().all()
    
    # 3. Construct Response
    final_url = ""
    if diary.image_s3_key:
        final_url = make_access_url(S3_BUCKET, diary.image_s3_key)
        
    panel_urls = []
    panels_data = []
    
    for chunk in chunks:
        # Get Image URL from metadata
        meta = chunk.metadata_ or {}
        key = meta.get("image_s3_key")
        p_url = ""
        if key:
            p_url = make_access_url(S3_BUCKET, key)
        elif meta.get("image_url"):
             p_url = meta.get("image_url") # Fallback
        
        panel_urls.append(p_url)
        panels_data.append(Panel(text=chunk.content))
        
    return ArtifactResponse(
        artifactId=str(diary.id),
        finalStripUrl=final_url,
        panelUrls=panel_urls,
        storyboard=Storyboard(panels=panels_data),
        stylePreset="comic", # Default for now
        createdAt=diary.created_at
    )
