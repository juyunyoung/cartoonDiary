from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import diary, artifacts, image, auth, users, jobs
from app.database import engine, Base

app = FastAPI()

# Database Initialization (for development with SQLite)
@app.on_event("startup")
async def startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
        # Safely add content_embedding column if it doesn't exist for vector search
        try:
            from sqlalchemy import text
            await conn.execute(text("ALTER TABLE diaries ADD COLUMN content_embedding JSON"))
            print("Added content_embedding column to diaries table.", flush=True)
        except Exception:
            # Column likely already exists
            pass

from fastapi import Request

@app.middleware("http")
async def log_requests(request: Request, call_next):
    import sys
    print(f"REQUEST: {request.method} {request.url.path}", flush=True)
    response = await call_next(request)
    print(f"RESPONSE: {response.status_code}", flush=True)
    return response

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000","http://amzn-s3-cdiary-images-01.s3-website-ap-northeast-1.amazonaws.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(diary.router, prefix="/api/diary", tags=["diary"])
app.include_router(image.router, prefix="/api/image", tags=["image"])
app.include_router(artifacts.router, prefix="/api/artifacts", tags=["artifacts"]) # Keeping this for now if needed
app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Cartoon Diary API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,  port=5050)
