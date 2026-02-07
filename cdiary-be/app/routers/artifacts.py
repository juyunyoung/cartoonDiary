from fastapi import APIRouter, HTTPException
from typing import List
from app.models.schemas import ArtifactResponse, ArtifactSummary, Storyboard

router = APIRouter(prefix="/api/artifacts", tags=["artifacts"])

@router.get("/", response_model=dict)
async def list_artifacts(limit: int = 20):
    # Mock data
    return {
        "items": [
            {
                "artifactId": "art_1",
                "thumbnailUrl": "https://via.placeholder.com/150",
                "date": "2024-02-07",
                "summary": "A funny day at the park.",
                "stylePreset": "cute"
            }
        ],
        "nextCursor": None
    }

@router.get("/{artifactId}", response_model=ArtifactResponse)
async def get_artifact(artifactId: str):
    # Mock data
    return {
        "artifactId": artifactId,
        "finalStripUrl": "https://via.placeholder.com/600x200",
        "panelUrls": [
            "https://via.placeholder.com/150",
            "https://via.placeholder.com/150",
            "https://via.placeholder.com/150",
            "https://via.placeholder.com/150"
        ],
        "storyboard": {
            "panels": [
                {"text": "Panel 1 text"},
                {"text": "Panel 2 text"},
                {"text": "Panel 3 text"},
                {"text": "Panel 4 text"}
            ]
        },
        "stylePreset": "cute",
        "createdAt": "2024-02-07T12:00:00Z"
    }
