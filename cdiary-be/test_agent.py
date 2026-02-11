import sys
import os
import time
import json
import threading

# Add current directory to path so we can import app modules properly
sys.path.append(os.getcwd())

from app.agent.worker import execute_job
from app.agent.store import get_job, create_job
from app.agent.models import JobStatus

def main():
    print("\n[Testing Agent Orchestration]")
    print("=" * 40)
    
    # Sample Diary Input
    diary_text = """
    오늘은 정말 운이 좋은 날이었다. 
    아침에 버스를 놓칠 뻔했는데 기사님이 기다려주셨다.
    점심에는 좋아하는 돈가스가 나와서 맛있게 먹었다.
    저녁에 집에 오니 강아지가 꼬리를 흔들며 반겨줬다.
    소소하지만 행복한 하루였다.
    """
    
    job_id = "test-job-demo"
    print(f"Job ID: {job_id}")
    print(f"Diary: {diary_text.strip()}")
    print("-" * 40)
    
    # 1. Initialize Job in Store
    create_job(JobStatus(job_id=job_id, status="QUEUED"))
    
    # 2. Run Job via Worker (in a separate thread to simulate async task)
    print("Starting worker...")
    t = threading.Thread(
        target=execute_job, 
        args=(job_id, diary_text, 4, "따뜻한 일상툰 스타일, 파스텔 톤, 귀여운 그림체", 1)
    )
    t.start()
    
    # 3. Monitor Progress
    while t.is_alive():
        job = get_job(job_id)
        if job:
            status_symbol = "..."
            if job.status == "RUNNING":
                status_symbol = "==>"
            elif job.status == "SUCCEEDED":
                status_symbol = "[OK]"
            elif job.status == "FAILED":
                status_symbol = "[XX]"
                
            print(f"\rStatus: {job.status} ({job.progress}%) {status_symbol}", end="")
            
            if job.error:
                print(f"\nError: {job.error}")
                break
                
        time.sleep(1)
        
    t.join()
    print("\n" + "=" * 40)
    
    # 4. Final Result Inspection
    job = get_job(job_id)
    print(f"Final Status: {job.status}")
    
    if job.storyboard:
        print("\n[Step 1: Generated Storyboard]")
        for cut in job.storyboard.cuts:
            summary = (cut.summary[:50] + '..') if len(cut.summary) > 50 else cut.summary
            print(f"- Cut {cut.cut_index}: {cut.scene} ({summary})")
            
    if job.prompts:
        print("\n[Step 2: Generated Prompts]")
        for p in job.prompts:
            prompt = (p.prompt[:60] + '..') if len(p.prompt) > 60 else p.prompt
            print(f"- Cut {p.cut_index}: {prompt}")
            
    if job.images:
        print("\n[Step 3: Generated Images]")
        for img in job.images:
            print(f"- Cut {img.cut_index}: {img.image_url}")
            if "s3_key" in img.meta:
                 print(f"  (S3 Key: {img.meta['s3_key']})")

    if job.qa_results:
        print("\n[Step 4: QA Results]")
        for r in job.qa_results:
            status_color = "PASS" if r.status == "PASS" else "FAIL"
            print(f"- Cut {r.cut_index}: {status_color}")
            if r.status == "FAIL":
                print(f"  Reason: {r.reason}")
                print(f"  Fix: {r.fix_hint}")

    if job.status == "SUCCEEDED":
        print("\nTest Completed Successfully! 🎉")
    else:
        print("\nTest Failed. Check errors above.")

if __name__ == "__main__":
    main()
