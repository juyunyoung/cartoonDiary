from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.models.schemas import DiaryEntryRequest, JobResponse
from app.services import ai_generator

router = APIRouter(prefix="/api", tags=["diary"])

@router.post("/generate", response_model=dict)
async def generate_comic(request: DiaryEntryRequest, background_tasks: BackgroundTasks):
    job_id = ai_generator.start_generation_job(request, background_tasks)
    return {"jobId": job_id}
