from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import datetime

from app.database import get_db
from app.models.models import Diary, DiaryChunk
from app.agent.bedrock import make_access_url, S3_BUCKET

router = APIRouter()

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
    diaryDate: datetime.date
    diaryText: str
    mood: Optional[str] = None
    options: Optional[Dict[str, Any]] = None

import math
from app.agent.bedrock import get_embedding

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    dot = sum(a*b for a, b in zip(v1, v2))
    n1 = math.sqrt(sum(a*a for a in v1))
    n2 = math.sqrt(sum(b*b for b in v2))
    if n1 == 0 or n2 == 0: return 0.0
    return dot / (n1 * n2)

@router.get("/", response_model=Dict[str, List[Any]])
async def list_artifacts(
    limit: int = 20, 
    query: Optional[str] = None, 
    user_id: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    # Simple list of recent diaries
    stmt = select(Diary).order_by(Diary.created_at.desc())
    
    if user_id:
        stmt = stmt.where(Diary.user_id == user_id)
        
    if not query:

        stmt = stmt.limit(limit)
        
    result = await db.execute(stmt)
    diaries = result.scalars().all()
    
    if query:
        print(f"DEBUG: Performing vector search for query: {query}", flush=True)
        try:
            q_emb = get_embedding(query)
            scored_diaries = []
            changed = False
            
            for d in diaries:
                # Generate missing embeddings on the fly
                if not d.content_embedding:
                    try:
                        d.content_embedding = get_embedding(d.content)
                        changed = True
                    except Exception as e:
                        print(f"DEBUG: Failed to embed diary {d.id}: {e}", flush=True)
                        continue
                
                if d.content_embedding:
                    score = cosine_similarity(q_emb, d.content_embedding)
                    scored_diaries.append((score, d))
                    
            if changed:
                await db.commit()
                
            # Sort by similarity score descending
            scored_diaries.sort(key=lambda x: x[0], reverse=True)
            
            # Filter results above an arbitrary semantic similarity threshold or just pick top N
            # A threshold of 0.25 is usually good for Amazon Titan Text Embeddings
            diaries = [d for score, d in scored_diaries if score > 0.25][:limit]
        except Exception as e:
            print(f"DEBUG: Vector search failed, falling back. Error: {e}", flush=True)
            # Fallback to simple matching if embeddings fail
            diaries = [d for d in diaries if query.lower() in d.content.lower()][:limit]
    
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
        stylePreset=diary.style_preset or "comic",
        createdAt=diary.created_at,
        diaryDate=diary.diary_date,
        diaryText=diary.content,
        mood=diary.mood,
        options=diary.generation_options
    )

@router.delete("/{artifact_id}")
async def delete_artifact(artifact_id: str, db: AsyncSession = Depends(get_db)):
    # 1. Fetch Diary
    stmt = select(Diary).where(Diary.id == artifact_id)
    result = await db.execute(stmt)
    diary = result.scalars().first()
    
    if not diary:
        raise HTTPException(status_code=404, detail="Artifact not found")
        
    # 2. Delete
    # Associated chunks should be deleted via cascade if configured in DB models, 
    # but explicit delete is safer if unsure about cascade configuration.
    # Assuming CASCADE is set on foreign keys in models or database.
    
    await db.delete(diary)
    await db.commit()
    
    return {"status": "success", "message": "Artifact deleted"}
