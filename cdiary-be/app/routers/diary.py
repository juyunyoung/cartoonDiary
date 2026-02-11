from fastapi import APIRouter, HTTPException, BackgroundTasks
import uuid
from app.agent.models import DiaryEntryRequest, JobStatus
from app.agent.worker import execute_job
from app.agent.store import create_job, get_job

router = APIRouter(prefix="/api/diary", tags=["diary"])

@router.post("/generate", response_model=JobStatus)
def generate_comic(diary_entry: DiaryEntryRequest, background_tasks: BackgroundTasks):
    try:
        job_id = uuid.uuid4().hex
        job = JobStatus(job_id=job_id, status="QUEUED", progress=0)
        create_job(job)

        # Start background job (agent worker)
        # Using default values for num_cuts, style_guide, max_retries for now
        # or we could extend DiaryEntryRequest to include them.
        background_tasks.add_task(
            execute_job, 
            job_id=job_id, 
            diary=diary_entry.diaryText, 
            num_cuts=4, 
            style_guide="따뜻한 파스텔 톤, 웹툰 느낌, 깔끔한 선, 감정이 잘 드러나는 표정", 
            max_retries=2
        )
        
        return job
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/jobs/{job_id}", response_model=JobStatus)
def get_comic_job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
