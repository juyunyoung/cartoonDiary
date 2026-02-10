from __future__ import annotations
import json
import uuid
from typing import List, Dict

from langgraph.graph import StateGraph, END
from .models import (
    OrchestrationState, Storyboard, StoryboardCut,
    ImagePrompt, CutImage, QAResult
)
from .bedrock import invoke_text_model, invoke_image_model_to_s3
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
        # job_id, cut_index passed for S3 naming
        out = invoke_image_model_to_s3(p.prompt, state.job_id, p.cut_index, width=1024, height=1024)
        
        images.append(CutImage(
            cut_index=p.cut_index, 
            image_url=out.url, 
            meta={"source": "bedrock", "s3_key": out.s3_key}
        ))

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
        out = invoke_image_model_to_s3(new_prompt, state.job_id, r.cut_index, width=1024, height=1024)
        for img in state.images:
            if img.cut_index == r.cut_index:
                img.image_url = out.url
                img.meta = {"source": "bedrock_retry", "s3_key": out.s3_key}

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
        return "{}" # Return empty dict as fallback or raise? Sample raises.
    return text[start:end + 1]


GRAPH = build_graph()


def run_job(state: OrchestrationState) -> OrchestrationState:
    return GRAPH.invoke(state)
