from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from pydantic import BaseModel
import uuid
import base64
import random
from app.agent.bedrock import generate_text_to_image, save_cut_image, save_profile_image
from app.database import get_db
from app.models.models import User

router = APIRouter()

class ImageGenerationRequest(BaseModel):
    prompt: str

@router.post("/generate")
async def generate_image(request: ImageGenerationRequest):
    try:
        # Call Bedrock
        seed = random.randint(0, 1000000)
        raw, img_bytes = generate_text_to_image(request.prompt, seed=seed)
        b64_img = base64.b64encode(img_bytes).decode("utf-8")
        
        return {
            "status": "success",
            "image_data": f"data:image/png;base64,{b64_img}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ImageSaveRequest(BaseModel):
    userId: str
    imageData: str

@router.post("/save")
async def save_image(request: ImageSaveRequest, db: AsyncSession = Depends(get_db)):
    try:
        # Decode base64 image
        if "," in request.imageData:
            b64_str = request.imageData.split(",")[1]
        else:
            b64_str = request.imageData
            
        img_bytes = base64.b64decode(b64_str)
        
        s3_key, url = save_profile_image(request.userId, img_bytes)
        
        # Update User in DB if exists (and userId is a valid UUID style string or matches DB)
        try:
            # Check if userId is a valid UUID, or just try query if using string ID
            stmt = select(User).where(User.id == request.userId)
            result = await db.execute(stmt)
            user = result.scalars().first()
            
            if user:
                user.profile_image_s3_key = s3_key
                await db.commit()
            else:
                 print(f"User {request.userId} not found in DB, skipping update.")

        except Exception as db_err:
            print(f"Failed to update DB: {db_err}")
            # Non-blocking for now
        
        return {
            "status": "success",
            "s3_key": s3_key,
            "image_url": url
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
