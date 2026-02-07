from fastapi import APIRouter, HTTPException
from app.models.schemas import DiaryEntryRequest, JobResponse
from app.services import ai_generator

router = APIRouter(prefix="/api", tags=["diary"])

@router.post("/generate", response_model=dict)
async def generate_comic(request: DiaryEntryRequest):
    job_id = ai_generator.start_generation_job(request)
    return {"jobId": job_id}
