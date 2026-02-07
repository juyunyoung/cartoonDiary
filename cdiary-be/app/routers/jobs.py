from fastapi import APIRouter, HTTPException
from app.models.schemas import JobResponse
from app.services import ai_generator

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

@router.get("/{jobId}", response_model=JobResponse)
async def get_job_status(jobId: str):
    status = ai_generator.get_job_status(jobId)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status
