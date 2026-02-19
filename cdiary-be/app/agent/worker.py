from __future__ import annotations
import uuid
import datetime
from typing import Optional
from sqlalchemy.future import select
from sqlalchemy import delete

from app.database import AsyncSessionLocal
from app.models.models import User, Diary, DiaryChunk
from app.routers.jobs import update_job, JobStatus

from .graph import run_job_async
from .models import OrchestrationState, DiaryEntryRequest
from .bedrock import S3_BUCKET, upload_bytes_to_s3
from app.utils.image import combine_images_vertically # Will create this utility

# Re-export execute_job for cleaner imports if needed, but here we define the main logic

async def execute_job(job_id: str, user_id: str, request: DiaryEntryRequest):
    print(f"[{job_id}] Starting agent execution for user {user_id}")
    
    try:
        # 1. Initialize Job & Create Placeholder Diary
        update_job(job_id, JobStatus.READING_DIARY, "Reading your diary...", 10)
        
        async with AsyncSessionLocal() as db:
            today = datetime.date.today()
            # Check existing diary
            stmt = select(Diary).where((Diary.user_id == user_id) & (Diary.diary_date == today))
            result = await db.execute(stmt)
            existing_diary = result.scalars().first()
            
            if existing_diary:
                db_diary = existing_diary
                db_diary.content = request.diaryText
                # Clear old chunks
                await db.execute(delete(DiaryChunk).where(DiaryChunk.diary_id == db_diary.id))
            else:
                db_diary = Diary(
                    id=uuid.UUID(job_id) if len(job_id) == 32 else uuid.uuid4(), # Try to use job_id as diary_id if UUID compatible? Or just let it generate. 
                    # Actually, if we use job_id as diary_id, it's easier to track? 
                    # job_id is hex string from uuid.uuid4().hex (32 chars). 
                    # Diary.id is GUID.
                    user_id=user_id,
                    diary_date=today,
                    content=request.diaryText,
                    image_s3_key=None # No image yet
                )
                db.add(db_diary)
            
            await db.commit()
            await db.refresh(db_diary)
            diary_id = str(db_diary.id)
            # Associate job with artifact immediately
            update_job(job_id, artifactId=diary_id)


        # 2. Fetch User Profile (if available) for consistency
        profile_ref_bytes = None
        async with AsyncSessionLocal() as db:
            try:
                stmt_user = select(User).where(User.id == user_id)
                res_user = await db.execute(stmt_user)
                user_obj = res_user.scalars().first()
                
                if user_obj and user_obj.profile_image_s3_key:
                    import boto3
                    s3 = boto3.client("s3")
                    if S3_BUCKET:
                         obj = s3.get_object(Bucket=S3_BUCKET, Key=user_obj.profile_image_s3_key)
                         profile_ref_bytes = obj["Body"].read()
                         print(f"Loaded profile image for reference: {len(profile_ref_bytes)} bytes")
            except Exception as e:
                print(f"Failed to load profile image: {e}")

        # 3. Create Orchestration State
        trace_id = uuid.uuid4().hex
        
        # Determine style guide based on preset
        style_guide = "Warm pastel tones, webtoon style, clean lines, expressive emotions"
        if request.stylePreset == "cute":
            style_guide = "Super cute, chibi style, soft colors, round shapes"
        elif request.stylePreset == "comedy":
            style_guide = "Exaggerated expressions, dynamic action, comic style, bright colors"
        elif request.stylePreset == "drama":
            style_guide = "Dramatic lighting, serious tone, detailed backgrounds, emotional"
        elif request.stylePreset == "minimal":
            style_guide = "Minimalist, simple lines, limited color palette, flat design"

        # Apply options
        if request.options and request.options.moreFunny:
            style_guide += ", humorous, funny situations"
        if request.options and request.options.focusEmotion:
            style_guide += ", focus on facial expressions and emotions"

        initial_state = OrchestrationState(
            job_id=job_id,
            diary=request.diaryText,
            num_cuts=4,
            style_guide=style_guide,
            max_retries=2,
            trace_id=trace_id,
            profile_image=profile_ref_bytes
        )

        # 4. Run the Graph (Agent)
        # The graph updates job progress/status internally via update_job
        final_state = await run_job_async(initial_state)
        
        # Determine if final_state is a dict (LangGraph behavior) and convert back to object
        if isinstance(final_state, dict):
            final_state = OrchestrationState(**final_state)
        
        # 5. Process Results (Save to DB)
        if not final_state.images:
             update_job(job_id, JobStatus.FAILED, "No images generated", 100, error="Agent failed to generate images")
             return

        update_job(job_id, JobStatus.COMPOSING_STRIP, "Finalizing...", 90)

        async with AsyncSessionLocal() as db:
            # Re-fetch diary to attach chunks
            stmt = select(Diary).where(Diary.id == diary_id)
            result = await db.execute(stmt)
            db_diary = result.scalars().first()
            
            if not db_diary:
                # Should not happen unless deleted
                print(f"CRITICAL: Diary {diary_id} disappeared during generation")
                return

            # Save Chunks
            panel_images_bytes = []
            
            # Ensure images are sorted by cut_index
            sorted_images = sorted(final_state.images, key=lambda x: x.cut_index)
            
            # Helper to find text for cut
            def get_cut_text(idx):
                if final_state.storyboard:
                    for c in final_state.storyboard.cuts:
                        if c.cut_index == idx:
                            return c.scene # or summary/dialogue?
                return ""

            for img in sorted_images:
                # We need to fetch the image bytes again? 
                # The graph saved to S3 and returned URLs.
                # To compose the strip, we need bytes.
                # Alternatively, we could have carried bytes in state but state size might be large.
                # Let's fetch from S3 or if we modifying graph to allow returning bytes?
                # For now, let's download from S3 using the key in meta.
                
                img_bytes = None
                s3_key = img.meta.get("s3_key")
                if s3_key:
                     import boto3
                     s3 = boto3.client("s3")
                     try:
                        obj = s3.get_object(Bucket=S3_BUCKET, Key=s3_key)
                        img_bytes = obj["Body"].read()
                        panel_images_bytes.append(img_bytes)
                     except Exception as e:
                         print(f"Failed to download image for composition: {e}")
                
                chunk = DiaryChunk(
                    diary_id=db_diary.id,
                    user_id=uuid.UUID(user_id),
                    chunk_index=img.cut_index,
                    content=get_cut_text(img.cut_index),
                    metadata_={
                        "image_s3_key": s3_key,
                        "image_url": img.image_url,
                        "source": img.meta.get("source")
                    }
                )
                db.add(chunk)
            
            await db.commit()

            # 6. Compose Strip
            if panel_images_bytes:
                final_strip_bytes = combine_images_vertically(panel_images_bytes)
                final_key = f"diary/{user_id}/{diary_id}/full_strip.png"
                
                if S3_BUCKET:
                    upload_bytes_to_s3(S3_BUCKET, final_key, final_strip_bytes, "image/png")
                    db_diary.image_s3_key = final_key
                    await db.commit()
            
            # 7. Done
            update_job(job_id, JobStatus.DONE, "Ready!", 100, artifactId=diary_id)
            print(f"[{job_id}] Execution complete. Artifact: {diary_id}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        update_job(job_id, JobStatus.FAILED, "Execution failed", 0, error=str(e))
