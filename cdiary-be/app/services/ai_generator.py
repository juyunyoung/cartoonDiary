import uuid
import time
from app.models.schemas import JobStatusEnum

# In-memory storage for jobs (replace with DB/Redis later)
jobs = {}

def start_generation_job(diary_entry):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "jobId": job_id,
        "status": JobStatusEnum.reading_diary,
        "step": "READING_DIARY",
        "progress": 0.0,
        "artifactId": None,
        "startTime": time.time()
    }
    # Simulate async processing in background would go here
    return job_id

def get_job_status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return None
    
    # Simulate progress (remove this in real implementation)
    elapsed = time.time() - job["startTime"]
    if elapsed < 2:
        job["status"] = JobStatusEnum.reading_diary
        job["progress"] = 0.1
    elif elapsed < 4:
        job["status"] = JobStatusEnum.building_storyboard
        job["progress"] = 0.3
    elif elapsed < 6:
        job["status"] = JobStatusEnum.generating_images
        job["progress"] = 0.6
    elif elapsed < 8:
        job["status"] = JobStatusEnum.composing_strip
        job["progress"] = 0.8
    else:
        job["status"] = JobStatusEnum.done
        job["progress"] = 1.0
        job["artifactId"] = f"art_{job_id}" # Mock artifact ID

    return job
