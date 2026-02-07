from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import diary, jobs, artifacts

app = FastAPI(title="Cartoon Diary API")

origins = [
    "http://localhost:5173", # Vite default port
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(diary.router)
app.include_router(jobs.router)
app.include_router(artifacts.router)

@app.get("/")
def read_root():
    return {"message": "Welcome to Cartoon Diary API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
