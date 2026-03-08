좋아요. “한 번에 잡아드리는” 기준으로, 바로 복붙해서 뼈대가 돌아가는 수준의 템플릿을 드릴게요. (LangGraph 감독 + 노드 내부에 Bedrock/Nova 호출 + QA/재시도 포함)

아래 코드는 실제 운영에서 제일 덜 아픈 패턴인
	•	FastAPI는 job 접수/조회만
	•	워커가 LangGraph 실행
으로 짰습니다.

⸻

0) 폴더 구조(추천)

cdiary-be/
  app/
    main.py                 # FastAPI
    graph.py                # LangGraph workflow
    models.py               # Pydantic state/IO schemas
    bedrock.py              # Bedrock 호출 래퍼(텍스트/이미지)
    store.py                # (임시) in-memory job store -> 나중에 DB로 교체
    worker.py               # 워커 엔트리포인트(데모)

1) requirements (대략)

pip install fastapi uvicorn pydantic langgraph langchain-core boto3


⸻

2) app/models.py — 상태/결과 스키마

from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Literal


class GenerateRequest(BaseModel):
    diary: str = Field(..., min_length=1)
    num_cuts: int = Field(default=4, ge=1, le=12)
    style_guide: str = Field(default="따뜻한 파스텔 톤, 웹툰 느낌, 깔끔한 선, 감정이 잘 드러나는 표정")
    max_retries: int = Field(default=2, ge=0, le=5)


class StoryboardCut(BaseModel):
    cut_index: int
    summary: str
    emotion: str
    scene: str
    dialogue: Optional[str] = None
    camera: Optional[str] = None


class Storyboard(BaseModel):
    cuts: List[StoryboardCut]


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


⸻

3) app/bedrock.py — Bedrock 호출 래퍼(자리 뼈대)

여기서는 “텍스트 모델 / 이미지 모델” 호출을 각각 함수로 빼놨어요.
Nova 모델 ID/리전은 환경에 맞게 채우면 됩니다.

from __future__ import annotations
import os
import json
import uuid
from typing import Any, Dict

import boto3


AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# 예시: 모델 ID는 환경변수로 주입(리전별로 다를 수 있으니)
NOVA_TEXT_MODEL_ID = os.getenv("NOVA_TEXT_MODEL_ID", "amazon.nova-lite-v1:0")
NOVA_IMAGE_MODEL_ID = os.getenv("NOVA_IMAGE_MODEL_ID", "amazon.nova-canvas-v1:0")  # 예시 이름


def _bedrock_runtime():
    return boto3.client("bedrock-runtime", region_name=AWS_REGION)


def invoke_text_model(prompt: str, temperature: float = 0.3) -> str:
    """
    반환은 '텍스트'라고 가정하는 간단 래퍼.
    실제 Nova 텍스트 API payload는 모델에 맞게 조정 필요.
    """
    br = _bedrock_runtime()
    body = {
        "inputText": prompt,
        "textGenerationConfig": {
            "temperature": temperature,
            "maxTokenCount": 2000,
        },
    }
    resp = br.invoke_model(
        modelId=NOVA_TEXT_MODEL_ID,
        body=json.dumps(body),
        accept="application/json",
        contentType="application/json",
    )
    data = json.loads(resp["body"].read())
    # 모델별 응답 포맷이 다를 수 있음: 여기서는 흔한 키를 우선 시도
    return (
        data.get("results", [{}])[0].get("outputText")
        or data.get("outputText")
        or json.dumps(data, ensure_ascii=False)
    )


def invoke_image_model(prompt: str, width: int = 1024, height: int = 1024) -> Dict[str, Any]:
    """
    이미지 생성: 보통 base64나 S3 업로드가 필요.
    여기서는 '생성 결과(가짜 URL)' 형태로 반환하는 뼈대.
    """
    br = _bedrock_runtime()
    body = {
        "prompt": prompt,
        "width": width,
        "height": height,
        # 모델에 따라 steps/seed/cfg 등 추가
    }
    resp = br.invoke_model(
        modelId=NOVA_IMAGE_MODEL_ID,
        body=json.dumps(body),
        accept="application/json",
        contentType="application/json",
    )
    data = json.loads(resp["body"].read())

    # TODO: data에서 base64 추출 -> S3 업로드 -> URL 생성
    fake_url = f"s3://your-bucket/jobs/{uuid.uuid4().hex}.png"
    return {"image_url": fake_url, "raw": data}


⸻

4) app/store.py — (임시) 잡 상태 저장소

지금은 인메모리. 운영에서는 DynamoDB/RDS/Redis로 교체하면 됩니다.

from __future__ import annotations
from typing import Dict
from threading import Lock
from .models import JobStatus

_jobs: Dict[str, JobStatus] = {}
_lock = Lock()


def create_job(job: JobStatus) -> None:
    with _lock:
        _jobs[job.job_id] = job


def get_job(job_id: str) -> JobStatus | None:
    with _lock:
        return _jobs.get(job_id)


def update_job(job_id: str, **kwargs) -> None:
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return
        updated = job.model_copy(update=kwargs)
        _jobs[job_id] = updated


⸻

5) app/graph.py — LangGraph 워크플로(핵심)

이게 “감독”입니다. 노드는 결정적으로(예측 가능하게) 구성하고,
LLM 호출은 노드 내부에서만.

from __future__ import annotations
import json
import uuid
from typing import List, Dict

from langgraph.graph import StateGraph, END
from .models import (
    OrchestrationState, Storyboard, StoryboardCut,
    ImagePrompt, CutImage, QAResult
)
from .bedrock import invoke_text_model, invoke_image_model
from .store import update_job


def _set_progress(state: OrchestrationState, progress: int, status: str | None = None, error: str | None = None):
    payload = {"progress": progress}
    if status:
        payload["status"] = status
    if error is not None:
        payload["error"] = error
    update_job(state.job_id, **payload)


def plan_storyboard(state: OrchestrationState) -> OrchestrationState:
    _set_progress(state, 10, status="RUNNING")

    prompt = f"""
너는 '일기 -> 만화 스토리보드' 편집자다.
아래 일기를 {state.num_cuts}컷 만화로 만들기 위한 스토리보드를 JSON으로만 출력해라.

요구 스키마:
{{
  "cuts": [
    {{
      "cut_index": 1,
      "summary": "...",
      "emotion": "...",
      "scene": "...",
      "dialogue": "...(없으면 null)",
      "camera": "...(없으면 null)"
    }}
  ]
}}

일기:
\"\"\"{state.diary}\"\"\"
"""
    raw = invoke_text_model(prompt, temperature=0.2)

    # 안전하게 JSON 파싱 시도 (모델이 종종 앞/뒤 말 붙임)
    json_str = _extract_json(raw)
    data = json.loads(json_str)

    sb = Storyboard(**data)
    state.storyboard = sb

    update_job(state.job_id, storyboard=sb)
    _set_progress(state, 25)
    return state


def build_prompts(state: OrchestrationState) -> OrchestrationState:
    assert state.storyboard is not None
    _set_progress(state, 35)

    prompts: List[ImagePrompt] = []
    for cut in state.storyboard.cuts:
        prompt = f"""
웹툰 한 컷을 생성하기 위한 이미지 프롬프트를 작성하라.
반드시 아래 스타일 가이드를 따른다:
- {state.style_guide}

컷 정보:
- 요약: {cut.summary}
- 감정: {cut.emotion}
- 장면: {cut.scene}
- 대사: {cut.dialogue}
- 카메라: {cut.camera}

출력은 한 줄 프롬프트 텍스트만.
"""
        p = invoke_text_model(prompt, temperature=0.3).strip()
        prompts.append(ImagePrompt(cut_index=cut.cut_index, prompt=p))

    state.prompts = prompts
    update_job(state.job_id, prompts=prompts)
    _set_progress(state, 45)
    return state


def generate_images(state: OrchestrationState) -> OrchestrationState:
    _set_progress(state, 60)

    images: List[CutImage] = []
    for p in state.prompts:
        out = invoke_image_model(p.prompt, width=1024, height=1024)
        images.append(CutImage(cut_index=p.cut_index, image_url=out["image_url"], meta={"source": "bedrock"}))

    state.images = images
    update_job(state.job_id, images=images)
    _set_progress(state, 75)
    return state


def qa_images(state: OrchestrationState) -> OrchestrationState:
    assert state.storyboard is not None
    _set_progress(state, 85)

    # 데모용 QA: 실제론 멀티모달로 이미지까지 보고 검사해야 함
    # 지금은 "프롬프트/스토리보드 정합성" 텍스트 검사 형태로만 뼈대
    qa_results: List[QAResult] = []
    cut_map: Dict[int, StoryboardCut] = {c.cut_index: c for c in state.storyboard.cuts}
    prompt_map: Dict[int, str] = {p.cut_index: p.prompt for p in state.prompts}

    for img in state.images:
        cut = cut_map[img.cut_index]
        ptxt = prompt_map[img.cut_index]

        qprompt = f"""
너는 만화 QA 담당이다. 아래 컷의 의도와 프롬프트가 일치하는지 검사해라.
PASS/FAIL로 판단하고, FAIL이면 reason과 fix_hint를 짧게 써라.
출력은 JSON만.

스키마:
{{"status":"PASS"|"FAIL","reason": "...","fix_hint":"..."}}

컷 의도:
- 요약: {cut.summary}
- 감정: {cut.emotion}
- 장면: {cut.scene}
- 대사: {cut.dialogue}
- 카메라: {cut.camera}

사용된 프롬프트:
{ptxt}
"""
        raw = invoke_text_model(qprompt, temperature=0.1)
        data = json.loads(_extract_json(raw))
        status = data.get("status", "FAIL")
        qa_results.append(QAResult(
            cut_index=img.cut_index,
            status=status,
            reason=data.get("reason"),
            fix_hint=data.get("fix_hint"),
        ))

    state.qa_results = qa_results
    update_job(state.job_id, qa_results=qa_results)
    return state


def retry_failed(state: OrchestrationState) -> OrchestrationState:
    failed = [r for r in state.qa_results if r.status == "FAIL"]
    if not failed:
        return state

    # 컷별 재시도
    for r in failed:
        cnt = state.retry_count.get(r.cut_index, 0)
        if cnt >= state.max_retries:
            continue

        # 프롬프트 수정
        old_prompt = next(p.prompt for p in state.prompts if p.cut_index == r.cut_index)
        revise_prompt = f"""
너는 이미지 프롬프트 리라이터다.
기존 프롬프트를 유지하되, QA 실패 사유를 해결하도록 프롬프트를 개선해라.
출력은 수정된 프롬프트 텍스트 한 줄만.

기존 프롬프트:
{old_prompt}

QA 실패 사유:
{r.reason}

수정 힌트:
{r.fix_hint}
"""
        new_prompt = invoke_text_model(revise_prompt, temperature=0.25).strip()

        # state 반영
        for p in state.prompts:
            if p.cut_index == r.cut_index:
                p.prompt = new_prompt

        # 이미지 재생성
        out = invoke_image_model(new_prompt, width=1024, height=1024)
        for img in state.images:
            if img.cut_index == r.cut_index:
                img.image_url = out["image_url"]

        state.retry_count[r.cut_index] = cnt + 1

    # 업데이트 반영 후 QA 다시 돌림(간단히 같은 노드를 재호출하기 위해 graph에서 루프)
    update_job(state.job_id, prompts=state.prompts, images=state.images)
    return state


def decide_next(state: OrchestrationState) -> str:
    # 실패 컷이 있고, 재시도 여지가 있으면 QA로 다시
    failed = [r for r in state.qa_results if r.status == "FAIL"]
    if not failed:
        return "done"

    for r in failed:
        if state.retry_count.get(r.cut_index, 0) < state.max_retries:
            return "recheck"
    return "done"


def done(state: OrchestrationState) -> OrchestrationState:
    # 최종 성공/실패 판정: 실패가 남아있으면 FAILED로 처리(정책에 따라 바꿀 수 있음)
    still_fail = any(r.status == "FAIL" for r in state.qa_results)
    if still_fail:
        update_job(state.job_id, status="FAILED", progress=100, error="Some cuts failed QA after retries.")
    else:
        update_job(state.job_id, status="SUCCEEDED", progress=100)
    return state


def build_graph():
    g = StateGraph(OrchestrationState)

    g.add_node("plan_storyboard", plan_storyboard)
    g.add_node("build_prompts", build_prompts)
    g.add_node("generate_images", generate_images)
    g.add_node("qa_images", qa_images)
    g.add_node("retry_failed", retry_failed)
    g.add_node("done", done)

    g.set_entry_point("plan_storyboard")
    g.add_edge("plan_storyboard", "build_prompts")
    g.add_edge("build_prompts", "generate_images")
    g.add_edge("generate_images", "qa_images")
    g.add_edge("qa_images", "retry_failed")

    g.add_conditional_edges(
        "retry_failed",
        decide_next,
        {
            "recheck": "qa_images",
            "done": "done",
        },
    )
    g.add_edge("done", END)

    return g.compile()


def _extract_json(text: str) -> str:
    """
    모델이 JSON 앞뒤로 말 붙이는 경우가 많아서,
    첫 '{'부터 마지막 '}'까지 잘라서 파싱합니다.
    """
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"JSON not found in model output: {text[:200]}")
    return text[start:end + 1]


GRAPH = build_graph()


def run_job(state: OrchestrationState) -> OrchestrationState:
    return GRAPH.invoke(state)


⸻

6) app/worker.py — 워커(데모)

실제 운영에서는 SQS/Celery/Step Functions로 돌리면 됩니다.
지금은 “job_id 받아서 실행”만.

from __future__ import annotations
import uuid
from .graph import run_job
from .models import OrchestrationState
from .store import update_job


def execute_job(job_id: str, diary: str, num_cuts: int, style_guide: str, max_retries: int):
    trace_id = uuid.uuid4().hex
    update_job(job_id, status="RUNNING", progress=1, error=None)

    state = OrchestrationState(
        job_id=job_id,
        diary=diary,
        num_cuts=num_cuts,
        style_guide=style_guide,
        max_retries=max_retries,
        trace_id=trace_id,
    )

    try:
        run_job(state)
    except Exception as e:
        update_job(job_id, status="FAILED", progress=100, error=str(e))
        raise


⸻

7) app/main.py — FastAPI (job 접수/조회)

“요청 → job_id 반환 → 워커가 실행” 패턴.
데모로는 background task를 썼지만, 운영에서는 분리 워커 추천.

from __future__ import annotations
import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException
from .models import GenerateRequest, JobStatus
from .store import create_job, get_job
from .worker import execute_job

app = FastAPI(title="Cartoon Diary Orchestrator")


@app.post("/generate", response_model=JobStatus)
def generate(req: GenerateRequest, bg: BackgroundTasks):
    job_id = uuid.uuid4().hex
    job = JobStatus(job_id=job_id, status="QUEUED", progress=0)
    create_job(job)

    # 데모용: 백그라운드로 실행(프로세스 분리 워커가 더 안전)
    bg.add_task(execute_job, job_id, req.diary, req.num_cuts, req.style_guide, req.max_retries)

    return get_job(job_id)


@app.get("/jobs/{job_id}", response_model=JobStatus)
def job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    return job


⸻

8) 실행 방법(데모)

uvicorn app.main:app --reload --port 8000

요청:

curl -X POST http://localhost:8000/generate \
  -H "Content-Type: application/json" \
  -d '{
    "diary":"오늘은 비가 와서 우산을 안 가져온 걸 후회했다. 점심에 친구가 우산을 빌려줘서 마음이 따뜻해졌다.",
    "num_cuts": 4,
    "style_guide":"따뜻한 색감, 캐릭터 표정 강조, 한국 웹툰 느낌",
    "max_retries": 2
  }'

조회:

curl http://localhost:8000/jobs/<job_id>


⸻

지금 템플릿에서 “딱 3군데”만 현실화하면 바로 프로덕션 각이 납니다
	1.	bedrock.py의 Nova 텍스트/이미지 payload + 응답 파싱을 실제 모델 포맷으로 확정
	2.	invoke_image_model()에서 base64 → S3 업로드 → https URL 반환
	3.	qa_images()를 멀티모달로 바꿔서 이미지 자체를 보고 QA (Nova 멀티모달/다른 VLM)

⸻
좋습니다. 아래는 **“이미지 결과(base64) → S3 업로드 → (선택) Presigned URL 반환”**까지 포함한 완성형 템플릿이에요.
단, 여기서 딱 한 가지는 솔직히 적어야 해요: Bedrock 이미지 모델마다 응답 JSON에서 base64가 들어있는 키 경로가 다를 수 있어서, _extract_base64_candidates()에서 여러 흔한 포맷을 다 커버하도록 만들어뒀습니다. (그래도 실제 사용 모델의 응답을 한 번 찍어서 키를 확정하면 가장 깔끔해집니다.)

아래대로 파일 교체/추가하면 됩니다.

⸻

1) 환경변수(.env 같은 곳)

AWS_REGION=us-east-1

# Bedrock 모델 ID (리전/계정에서 실제 사용 가능한 ID로)
NOVA_TEXT_MODEL_ID=amazon.nova-lite-v1:0
NOVA_IMAGE_MODEL_ID=amazon.nova-canvas-v1:0

# S3
S3_BUCKET=your-bucket-name
S3_PREFIX=cartoon-diary
S3_PUBLIC=false              # true면 public-read로 업로드(비추천)
S3_PRESIGN_EXPIRE_SECONDS=3600
S3_SSE=AES256                # 서버사이드 암호화(권장) / 또는 aws:kms
S3_KMS_KEY_ID=               # SSE=aws:kms일 때 사용 (선택)


⸻

2) app/bedrock.py (완성형) — Bedrock 호출 + base64 추출 + S3 업로드

from __future__ import annotations

import base64
import binascii
import json
import os
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import boto3
from botocore.exceptions import ClientError


AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

NOVA_TEXT_MODEL_ID = os.getenv("NOVA_TEXT_MODEL_ID", "amazon.nova-lite-v1:0")
NOVA_IMAGE_MODEL_ID = os.getenv("NOVA_IMAGE_MODEL_ID", "amazon.nova-canvas-v1:0")

S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_PREFIX = os.getenv("S3_PREFIX", "cartoon-diary").strip("/")
S3_PUBLIC = os.getenv("S3_PUBLIC", "false").lower() == "true"
S3_PRESIGN_EXPIRE_SECONDS = int(os.getenv("S3_PRESIGN_EXPIRE_SECONDS", "3600"))
S3_SSE = os.getenv("S3_SSE", "AES256")  # AES256 or aws:kms
S3_KMS_KEY_ID = os.getenv("S3_KMS_KEY_ID", "").strip() or None


def _bedrock_runtime():
    return boto3.client("bedrock-runtime", region_name=AWS_REGION)


def _s3():
    return boto3.client("s3", region_name=AWS_REGION)


def invoke_text_model(prompt: str, temperature: float = 0.3) -> str:
    """
    NOTE: Nova 텍스트 모델의 정확한 payload/응답 포맷은 모델 버전에 따라 달라질 수 있어요.
    여기선 "inputText" + "textGenerationConfig" 형태를 기본으로 둡니다.
    """
    br = _bedrock_runtime()
    body = {
        "inputText": prompt,
        "textGenerationConfig": {
            "temperature": temperature,
            "maxTokenCount": 2000,
        },
    }
    resp = br.invoke_model(
        modelId=NOVA_TEXT_MODEL_ID,
        body=json.dumps(body),
        accept="application/json",
        contentType="application/json",
    )
    data = json.loads(resp["body"].read())

    # 여러 포맷 방어
    return (
        data.get("results", [{}])[0].get("outputText")
        or data.get("outputText")
        or data.get("generation")
        or json.dumps(data, ensure_ascii=False)
    )


@dataclass
class ImageInvokeResult:
    s3_key: str
    s3_uri: str
    url: str  # public url or presigned url
    raw: Dict[str, Any]


def invoke_image_model_to_s3(
    prompt: str,
    job_id: str,
    cut_index: int,
    width: int = 1024,
    height: int = 1024,
) -> ImageInvokeResult:
    """
    Bedrock 이미지 모델 호출 -> 응답에서 base64 추출 -> S3 업로드 -> URL 반환(공개 또는 presigned)
    """
    if not S3_BUCKET:
        raise RuntimeError("S3_BUCKET env var is required")

    br = _bedrock_runtime()

    # NOTE: 모델별 payload 차이가 큼. 아래는 예시.
    # 실제 Nova/Canvas 모델의 공식 payload로 조정 필요할 수 있음.
    body = {
        "prompt": prompt,
        "width": width,
        "height": height,
    }

    resp = br.invoke_model(
        modelId=NOVA_IMAGE_MODEL_ID,
        body=json.dumps(body),
        accept="application/json",
        contentType="application/json",
    )
    raw = json.loads(resp["body"].read())

    # 1) base64 후보들 수집
    b64_list = _extract_base64_candidates(raw)
    if not b64_list:
        # 모델이 base64를 안 주고 S3/URL을 주는 타입일 수도 있음
        # 그 경우 raw 안에서 URL/URI를 찾아 반환하는 fallback도 가능하지만,
        # 여기선 명확히 에러를 내서 응답 포맷을 확인하도록 유도합니다.
        raise ValueError(f"No base64 image found in response keys. Raw keys={list(raw.keys())}")

    # 2) 첫 번째 유효 base64를 디코드
    img_bytes, ext, content_type = _decode_first_valid_image(b64_list)

    # 3) S3 업로드
    file_id = uuid.uuid4().hex
    s3_key = f"{S3_PREFIX}/jobs/{job_id}/cut-{cut_index:02d}-{file_id}.{ext}"
    _upload_bytes_to_s3(
        bucket=S3_BUCKET,
        key=s3_key,
        data=img_bytes,
        content_type=content_type,
    )

    s3_uri = f"s3://{S3_BUCKET}/{s3_key}"
    url = _make_access_url(S3_BUCKET, s3_key)

    return ImageInvokeResult(
        s3_key=s3_key,
        s3_uri=s3_uri,
        url=url,
        raw=raw,
    )


def _extract_base64_candidates(raw: Any) -> List[str]:
    """
    모델 응답에서 base64 문자열 후보를 최대한 광범위하게 찾아냅니다.
    흔한 케이스:
    - {"images":[{"base64":"..."}]}
    - {"artifacts":[{"base64":"...","mimeType":"image/png"}]}
    - {"image":"..."} / {"base64":"..."} / {"data":"..."}
    - 중첩 구조
    """
    candidates: List[str] = []

    def walk(x: Any):
        if isinstance(x, dict):
            for k, v in x.items():
                lk = k.lower()
                if lk in ("base64", "b64", "image", "image_base64", "imagebase64", "data"):
                    if isinstance(v, str) and len(v) > 100:  # 짧은 건 제외
                        candidates.append(v)
                walk(v)
        elif isinstance(x, list):
            for it in x:
                walk(it)

    walk(raw)

    # data:image/png;base64,.... 형태도 대비
    cleaned: List[str] = []
    for c in candidates:
        if c.startswith("data:image/"):
            # data:image/png;base64,AAAA...
            comma = c.find(",")
            if comma != -1:
                cleaned.append(c[comma + 1 :])
        else:
            cleaned.append(c)

    # 중복 제거(순서 유지)
    seen = set()
    uniq = []
    for c in cleaned:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq


def _decode_first_valid_image(b64_list: List[str]) -> Tuple[bytes, str, str]:
    """
    base64를 디코드해서 PNG/JPEG 여부를 매직바이트로 판정합니다.
    """
    for b64s in b64_list:
        b64s_stripped = b64s.strip().replace("\n", "").replace("\r", "")
        # 패딩 보정
        pad = len(b64s_stripped) % 4
        if pad:
            b64s_stripped += "=" * (4 - pad)

        try:
            data = base64.b64decode(b64s_stripped, validate=False)
        except (binascii.Error, ValueError):
            continue

        # PNG signature: 89 50 4E 47 0D 0A 1A 0A
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return data, "png", "image/png"

        # JPEG signature: FF D8 ... FF D9
        if data[:2] == b"\xff\xd8":
            return data, "jpg", "image/jpeg"

        # WebP: "RIFF"...."WEBP"
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            return data, "webp", "image/webp"

        # 그래도 이미지일 수 있지만 모르면 png로 저장(비추) 대신 다음 후보 탐색
        continue

    raise ValueError("No decodable PNG/JPEG/WEBP found among base64 candidates.")


def _upload_bytes_to_s3(bucket: str, key: str, data: bytes, content_type: str):
    s3 = _s3()
    extra_args: Dict[str, Any] = {
        "ContentType": content_type,
        "CacheControl": "max-age=31536000, immutable",
    }

    # SSE
    if S3_SSE:
        extra_args["ServerSideEncryption"] = S3_SSE
        if S3_SSE == "aws:kms" and S3_KMS_KEY_ID:
            extra_args["SSEKMSKeyId"] = S3_KMS_KEY_ID

    # 공개 업로드는 운영에선 비추천(대신 presigned 권장)
    if S3_PUBLIC:
        extra_args["ACL"] = "public-read"

    try:
        s3.put_object(Bucket=bucket, Key=key, Body=data, **extra_args)
    except ClientError as e:
        raise RuntimeError(f"S3 put_object failed: {e}")


def _make_access_url(bucket: str, key: str) -> str:
    """
    S3_PUBLIC=true면 정적 URL, 아니면 presigned URL.
    """
    if S3_PUBLIC:
        # Virtual-hosted-style URL
        return f"https://{bucket}.s3.{AWS_REGION}.amazonaws.com/{key}"

    s3 = _s3()
    try:
        return s3.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=S3_PRESIGN_EXPIRE_SECONDS,
        )
    except ClientError as e:
        raise RuntimeError(f"presign failed: {e}")


⸻

3) app/graph.py 수정 — 이미지 생성 노드를 S3 업로드 버전으로 교체

기존 generate_images()만 아래처럼 바꿔주세요.

def generate_images(state: OrchestrationState) -> OrchestrationState:
    _set_progress(state, 60)

    images: List[CutImage] = []
    for p in state.prompts:
        out = invoke_image_model_to_s3(
            prompt=p.prompt,
            job_id=state.job_id,
            cut_index=p.cut_index,
            width=1024,
            height=1024,
        )
        images.append(
            CutImage(
                cut_index=p.cut_index,
                image_url=out.url,              # presigned or public url
                meta={"s3_key": out.s3_key, "s3_uri": out.s3_uri, "source": "bedrock"},
            )
        )

    state.images = images
    update_job(state.job_id, images=images)
    _set_progress(state, 75)
    return state

그리고 retry_failed() 안에서 이미지 재생성하는 부분도 같은 함수를 쓰도록 바꿔주세요:

        out = invoke_image_model_to_s3(
            prompt=new_prompt,
            job_id=state.job_id,
            cut_index=r.cut_index,
            width=1024,
            height=1024,
        )
        for img in state.images:
            if img.cut_index == r.cut_index:
                img.image_url = out.url
                img.meta.update({"s3_key": out.s3_key, "s3_uri": out.s3_uri})


⸻

4) IAM 권한(최소)

실행 역할(예: App Runner/ECS/EC2 role)에 아래가 필요합니다.
	•	Bedrock invoke
	•	bedrock:InvokeModel
	•	S3 업로드 + presign용 조회
	•	s3:PutObject
	•	s3:GetObject (presigned URL 발급 시 실질적으로는 서명만 하지만, 운영 정책상 GetObject 권한을 함께 주는 게 일반적)
	•	(선택) s3:PutObjectAcl (S3_PUBLIC=true 일 때만 필요)

SSE-KMS를 쓰면 추가로:
	•	kms:Encrypt, kms:Decrypt(보통 presigned로 내려받을 때 decrypt 필요), kms:GenerateDataKey

⸻

5) 이 “완성형”이 이미 해결한 운영 이슈들
	•	이미지가 base64로 와도 S3에 표준 아카이브 (job_id/cut 기반 키)
	•	공개 업로드를 피하고 Presigned URL 기본값으로 안전하게 전달
	•	응답 포맷이 조금 달라도 base64 키 경로를 넓게 커버

⸻

6) 마지막으로, 모델 응답 포맷을 100% 확정하고 싶으면

운영 안정성을 위해 딱 한 번만 해보면 좋습니다:
	•	invoke_image_model_to_s3()에서 raw를 로그로 찍거나(민감정보 주의)
	•	base64가 실제로 어디에 있는지 확인해서
	•	_extract_base64_candidates()를 “그 모델에 최적화된 키 경로”로 좁히면
실패율이 더 내려갑니다.

⸻

