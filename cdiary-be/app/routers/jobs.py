from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum

router = APIRouter(prefix="/api/jobs", tags=["jobs"])

class JobStatus(str, Enum):
    READING_DIARY = "READING_DIARY"
    BUILDING_STORYBOARD = "BUILDING_STORYBOARD"
    GENERATING_IMAGES = "GENERATING_IMAGES"
    COMPOSING_STRIP = "COMPOSING_STRIP"
    DONE = "DONE"
    FAILED = "FAILED"

class JobResponse(BaseModel):
    jobId: str
    status: JobStatus
    step: str
    progress: float
    artifactId: Optional[str] = None
    error: Optional[str] = None

# In-memory job store
# Structure: { jobId: { "status": ..., "step": ..., "progress": ..., "artifactId": ..., "error": ... } }
JOBS: Dict[str, Dict[str, Any]] = {}

@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str):
    print(f"Fetching job status for: {job_id}")
    job = JOBS.get(job_id)
    if not job:
        print(f"Job {job_id} NOT FOUND. Active jobs: {list(JOBS.keys())}")
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobResponse(
        jobId=job_id,
        status=job["status"],
        step=job.get("step", ""),
        progress=job.get("progress", 0.0),
        artifactId=job.get("artifactId"),
        error=job.get("error")
    )

def update_job(job_id: str, status: JobStatus, step: str, progress: float, artifact_id: Optional[str] = None, error: Optional[str] = None):
    if job_id in JOBS:
        JOBS[job_id]["status"] = status
        JOBS[job_id]["step"] = step
        JOBS[job_id]["progress"] = progress
        if artifact_id:
            JOBS[job_id]["artifactId"] = artifact_id
        if error:
            JOBS[job_id]["error"] = error
            JOBS[job_id]["status"] = JobStatus.FAILED

def create_job(job_id: str):
    print(f"Creating new job: {job_id}")
    JOBS[job_id] = {
        "status": JobStatus.READING_DIARY,
        "step": "Starting...",
        "progress": 0.0,
        "artifactId": None,
        "error": None
    }
