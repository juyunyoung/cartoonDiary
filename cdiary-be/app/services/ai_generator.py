import uuid
import time
import threading
from app.models.schemas import JobStatusEnum, DiaryEntryRequest
from app.services.nova_service import nova_service

# In-memory storage for jobs (replace with DB/Redis later)
jobs = {}

def start_generation_job(diary_entry: DiaryEntryRequest) -> str:
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
    
    # Start background thread
    thread = threading.Thread(target=process_job, args=(job_id, diary_entry.diaryText))
    thread.daemon = True # Daemonize thread
    thread.start()
    
    return job_id

def process_job(job_id: str, text: str):
    job = jobs.get(job_id)
    if not job:
        return

    try:
        # Step 1: Reading Diary
        job["status"] = JobStatusEnum.reading_diary
        job["progress"] = 0.1
        time.sleep(1) # simulate parsing if ANY

        # Step 2: Storyboard (Skipped for now, mock)
        job["status"] = JobStatusEnum.building_storyboard
        job["progress"] = 0.3
        time.sleep(1)

        # Step 3: Generating Images
        job["status"] = JobStatusEnum.generating_images
        job["progress"] = 0.5
        
        # Synchronous call since we are in a thread
        if nova_service:
            # Simple prompt for now: just the diary text
            prompt = f"A comic strip panel, cartoon style: {text[:200]}" 
            image_bytes = nova_service.generate_image(prompt)
            
            if image_bytes:
                # Mock saving
                pass 
            else:
                # In a real app we might fail here, or just log config usage
                # For this demo, if no bytes, we proceed or error?
                # NovaService returns None on error.
                raise Exception("Failed to generate image from Nova")
        else:
            raise Exception("Nova Service not initialized")

        job["progress"] = 0.8

        # Step 4: Composing
        job["status"] = JobStatusEnum.composing_strip
        time.sleep(1)
        
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
