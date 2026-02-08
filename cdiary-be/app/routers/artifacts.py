from fastapi import APIRouter

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])

# Implementation pending actual logic, keeping it minimal as per original file structure likely
# Original file content was small, just placeholder usually.

@router.get("/")
def list_artifacts():
    return []
