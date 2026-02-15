from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
import base64
from app.agent.bedrock import generate_text_to_image, save_cut_image

router = APIRouter()

class ImageGenerationRequest(BaseModel):
    prompt: str

@router.post("/generate")
async def generate_image(request: ImageGenerationRequest):
    try:
        
        # Call Bedrock
        raw, img_bytes = generate_text_to_image(request.prompt)
        b64_img = base64.b64encode(img_bytes).decode("utf-8")
        
        return {
            "status": "success",
            "image_data": f"data:image/png;base64,{b64_img}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
