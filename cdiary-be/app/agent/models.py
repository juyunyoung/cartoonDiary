from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal


class GenerateRequest(BaseModel):
    diary: str = Field(..., min_length=1)
    num_cuts: int = Field(default=4, ge=1, le=12)
    style_guide: str = Field(default="따뜻한 파스텔 톤, 웹툰 느낌, 깔끔한 선, 감정이 잘 드러나는 표정")
    max_retries: int = Field(default=2, ge=0, le=5)


# --- API Schemas (Moved from app/models) ---
from enum import Enum

class StylePreset(str, Enum):
    CUTE = "cute"
    COMEDY = "comedy"
    DRAMA = "drama"
    MINIMAL = "minimal"

class GenerationOptions(BaseModel):
    moreFunny: bool = False
    focusEmotion: bool = False
    lessText: bool = False

class DiaryEntryRequest(BaseModel):
    diaryText: str
    mood: str
    stylePreset: StylePreset
    protagonistName: Optional[str] = "Me"
    options: GenerationOptions
# -------------------------------------------


class StoryboardCut(BaseModel):
    cut_index: int
    summary: str
    emotion: str
    scene: str
    dialogue: Optional[str] = None
    camera: Optional[str] = None


class Storyboard(BaseModel):
    cuts: List[StoryboardCut]
    character_appearance: Optional[str] = None


class ImagePrompt(BaseModel):
    cut_index: int
    prompt: str


class QAResult(BaseModel):
    cut_index: int
    status: Literal["PASS", "FAIL"]
    reason: Optional[str] = None
    fix_hint: Optional[str] = None


class CutImage(BaseModel):
    cut_index: int
    image_url: str
    meta: Dict[str, str] = Field(default_factory=dict)


class JobStatus(BaseModel):
    job_id: str
    status: Literal["QUEUED", "RUNNING", "SUCCEEDED", "FAILED"]
    progress: int = 0  # 0~100
    error: Optional[str] = None

    storyboard: Optional[Storyboard] = None
    prompts: Optional[List[ImagePrompt]] = None
    images: Optional[List[CutImage]] = None
    qa_results: Optional[List[QAResult]] = None


class OrchestrationState(BaseModel):
    # input
    job_id: str
    diary: str
    num_cuts: int
    style_guide: str
    max_retries: int

    # working
    storyboard: Optional[Storyboard] = None
    prompts: List[ImagePrompt] = Field(default_factory=list)
    images: List[CutImage] = Field(default_factory=list)
    qa_results: List[QAResult] = Field(default_factory=list)

    # retry tracking
    retry_count: Dict[int, int] = Field(default_factory=dict)  # cut_index -> retries

    # observability
    trace_id: str
