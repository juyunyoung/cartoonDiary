from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any
from enum import Enum
from fastapi import Depends
from app.auth.security import get_current_user

router = APIRouter()

class JobStatus(str, Enum):
    READING_DIARY = "READING_DIARY"
    BUILDING_STORYBOARD = "BUILDING_STORYBOARD"
    GENERATING_IMAGES = "GENERATING_IMAGES"
    COMPOSING_STRIP = "COMPOSING_STRIP"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
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

import logging
import sys

import asyncio
import json
from fastapi.responses import StreamingResponse
from fastapi.encoders import jsonable_encoder

# logger = logging.getLogger("uvicorn") # Switching to print for visibility

@router.get("/stream")
async def stream_jobs(current_user: dict = Depends(get_current_user)):
    """Server-Sent Events endpoint to stream active jobs state."""
    user_id = current_user["id"]
    async def event_generator():
        while True:
            # Filter jobs for current user only
            current_jobs = {k: v for k, v in JOBS.items() if v.get("userId") == user_id}
            yield f"data: {json.dumps(jsonable_encoder(current_jobs))}\n\n"
            await asyncio.sleep(1)
            
    return StreamingResponse(
        event_generator(), 
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no" # Disable buffering for Nginx if any
        }
    )


@router.get("/debug", response_model=Dict[str, Any])
async def debug_jobs():
    print(f"DEBUG: Current Jobs: {list(JOBS.keys())} (JOBS ID: {id(JOBS)})", flush=True)
    return JOBS

@router.get("/{job_id}", response_model=JobResponse)
async def get_job_status(job_id: str, current_user: dict = Depends(get_current_user)):
    print(f"Fetching job status for: {job_id} from JOBS {id(JOBS)}", flush=True)
    job = JOBS.get(job_id)
    if not job:
        # ... existing not found logic ...
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job.get("userId") != current_user["id"]:
        raise HTTPException(status_code=403, detail="Not authorized to view this job")
    
    return JobResponse(
        jobId=job_id,
        status=job["status"],
        step=job.get("step", ""),
        progress=job.get("progress", 0.0),
        artifactId=job.get("artifactId"),
        error=job.get("error")
    )

def update_job(job_id: str, status: Optional[JobStatus] = None, step: Optional[str] = None, progress: Optional[float] = None, artifact_id: Optional[str] = None, error: Optional[str] = None, **kwargs):
    # print(f"DEBUG: Updating job {job_id} in {id(JOBS)}")
    if job_id not in JOBS:
        print(f"WARNING: Attempted to update non-existent job {job_id} in JOBS {id(JOBS)}", flush=True)
        return

    updates = kwargs.copy()
    if status is not None: updates["status"] = status
    if step is not None: updates["step"] = step
    if progress is not None: updates["progress"] = progress
    if artifact_id is not None: updates["artifactId"] = artifact_id
    if error is not None: 
        updates["error"] = error
        updates["status"] = JobStatus.FAILED

    # Handle alias just in case
    if 'artifact_id' in updates:
        updates['artifactId'] = updates.pop('artifact_id')
    
    # Merge updates
    JOBS[job_id].update(updates)


def create_job(job_id: str, user_id: Optional[str] = None, artifact_id: Optional[str] = None):
    print(f"Creating new job: {job_id} for user {user_id}", flush=True)
    JOBS[job_id] = {
        "userId": user_id,
        "status": JobStatus.READING_DIARY,
        "step": "Starting...",
        "progress": 0.0,
        "artifactId": artifact_id,
        "error": None
    }
