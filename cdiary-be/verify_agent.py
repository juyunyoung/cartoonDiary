import sys
import os
import time
import threading

# Add current directory to path so we can import app
sys.path.append(os.getcwd())

from app.agent.worker import execute_job
from app.agent.store import get_job, create_job
from app.agent.models import JobStatus

def main():
    print("Starting Agent Verification...")
    
    diary_text = "오늘은 친구와 공원에 갔다. 날씨가 정말 좋아서 기분이 상쾌했다. 벤치에 앉아서 아이스크림을 먹었는데, 비둘기가 다가와서 조금 무서웠다."
    job_id = "test-job-verification"
    
    # Init job in store
    create_job(JobStatus(job_id=job_id, status="QUEUED"))
    
    # Run in thread to simulate background task
    t = threading.Thread(target=execute_job, args=(job_id, diary_text, 4, "webtoon style", 2))
    t.start()
    
    # Monitor
    while t.is_alive():
        job = get_job(job_id)
        if job:
            print(f"Status: {job.status}, Progress: {job.progress}%")
            if job.error:
                print(f"Error: {job.error}")
        time.sleep(2)
        
    t.join()
    
    # Final check
    job = get_job(job_id)
    print(f"Final Status: {job.status}")
    if job.images:
        print(f"Generated {len(job.images)} images.")
        for img in job.images:
            print(f"- Cut {img.cut_index}: {img.image_url}")
            
    if job.status == "FAILED":
        print(f"Job Failed: {job.error}")
        sys.exit(1)
    else:
        print("Verification Successful!")

if __name__ == "__main__":
    main()
