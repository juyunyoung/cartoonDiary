import uuid
import time
import asyncio
from app.models.schemas import JobStatusEnum, DiaryEntryRequest
from fastapi import BackgroundTasks
from app.services.nova_service import nova_service

# In-memory storage for jobs (replace with DB/Redis later)
jobs = {}

def start_generation_job(diary_entry: DiaryEntryRequest, background_tasks: BackgroundTasks) -> str:
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "jobId": job_id,
        "status": JobStatusEnum.reading_diary,
        "step": "READING_DIARY",
        "progress": 0.0,
        "artifactId": None,
        "startTime": time.time(),
        "error": None
    }
    
    background_tasks.add_task(process_job, job_id, diary_entry.diaryText)
    return job_id

async def process_job(job_id: str, text: str):
    job = jobs.get(job_id)
    if not job:
        return

    try:
        # Step 1: Reading Diary
        job["status"] = JobStatusEnum.reading_diary
        job["progress"] = 0.1
        await asyncio.sleep(1) # simulate parsing if ANY

        # Step 2: Storyboard (Skipped for now, mock)
        job["status"] = JobStatusEnum.building_storyboard
        job["progress"] = 0.3
        await asyncio.sleep(1)

        # Step 3: Generating Images
        job["status"] = JobStatusEnum.generating_images
        job["progress"] = 0.5
        
        loop = asyncio.get_event_loop()
        # Use run_in_executor to avoid blocking the event loop with synchronous boto3 call
        if nova_service:
            # Simple prompt for now: just the diary text
            # In production, we'd use an LLM to summarize/describe scene first.
            prompt = f"A comic strip panel, cartoon style: {text[:200]}" 
            image_bytes = await loop.run_in_executor(None, nova_service.generate_image, prompt)
            
            if image_bytes:
                # Mock saving - in real app, save to file/S3
                # For now, just mark success.
                pass 
            else:
                raise Exception("Failed to generate image from Nova")
        else:
            raise Exception("Nova Service not initialized")

        job["progress"] = 0.8

        # Step 4: Composing
        job["status"] = JobStatusEnum.composing_strip
        await asyncio.sleep(1)
        
        # Done
        job["status"] = JobStatusEnum.done
        job["progress"] = 1.0
        job["artifactId"] = f"art_{job_id}" # Mock artifact ID

    except Exception as e:
        print(f"Job {job_id} failed: {e}")
        job["status"] = JobStatusEnum.failed
        job["error"] = str(e)

def get_job_status(job_id: str):
    return jobs.get(job_id)
