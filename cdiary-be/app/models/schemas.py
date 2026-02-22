from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum
import datetime

from app.agent.models import StylePreset, GenerationOptions, DiaryEntryRequest

class JobStatusEnum(str, Enum):
    reading_diary = "READING_DIARY"
    building_storyboard = "BUILDING_STORYBOARD"
    generating_images = "GENERATING_IMAGES"
    composing_strip = "COMPOSING_STRIP"
    done = "DONE"
    failed = "FAILED"

class JobResponse(BaseModel):
    jobId: str
    status: JobStatusEnum
    step: str
    progress: float
    artifactId: Optional[str] = None
    error: Optional[str] = None

class Panel(BaseModel):
    panelId: int
    imageUrl: str
    description: str

class Storyboard(BaseModel):
    panels: List[Dict[str, Any]]

class ArtifactResponse(BaseModel):
    artifactId: str
    finalStripUrl: str
    panelUrls: List[str]
    storyboard: Storyboard
    stylePreset: str
    createdAt: str

class ArtifactSummary(BaseModel):
    artifactId: str
    thumbnailUrl: str
    date: str
    summary: str
    stylePreset: str
