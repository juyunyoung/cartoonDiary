from fastapi import APIRouter, HTTPException
from app.models.schemas import DiaryEntryRequest
from app.services import ai_generator

router = APIRouter(prefix="/api/diary", tags=["diary"])

@router.post("/generate")
def generate_comic(diary_entry: DiaryEntryRequest):
    try:
        print(generate_comic)
        # Start background job (threading)
        job_id = ai_generator.start_generation_job(diary_entry)
        
        return {"jobId": job_id}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
