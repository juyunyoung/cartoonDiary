from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import diary, artifacts, image

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(diary.router)
app.include_router(artifacts.router)
app.include_router(image.router, prefix="/api/image", tags=["image"])

@app.get("/")
def read_root():
    return {"message": "Welcome to Cartoon Diary API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,  port=5050)
