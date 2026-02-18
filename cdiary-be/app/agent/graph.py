from __future__ import annotations
import json
import uuid
from typing import List, Dict

from langgraph.graph import StateGraph, END
from .models import (
    OrchestrationState, Storyboard, StoryboardCut,
    ImagePrompt, CutImage, QAResult
)
from .bedrock import invoke_text_model, invoke_image_model_to_s3, save_cut_image
from .store import update_job
import io
from PIL import Image


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
        You are a professional 'Diary to Comic Storyboard' editor.
        Create a {state.num_cuts}-cut comic storyboard from the diary below.
        Output MUST be in JSON format only.

        Required Schema:
        {{
        "character_appearance": "Concise description of the main character (max 10 words, e.g., 'Boy with glasses in hoodie')",
        "cuts": [
            {{
            "cut_index": 1,
            "summary": "Short summary of the scene",
            "emotion": "Dominant emotion",
            "scene": "Visual scene description",
            "dialogue": "Character dialogue (or null if none)",
            "camera": "Camera angle/shot type (or null if none)"
            }}
        ]
        }}

        Diary:
        \"\"\"{state.diary}\"\"\"

        Ensure all content in the JSON (summary, scene, etc.) is written in English.
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
            Write an image generation prompt for a webtoon panel.
            You must strictly follow the style guide below:
            - {state.style_guide}

            Few-Shot Examples (Focus on location and action):
            Panel 1 (BUS STOP OUTSIDE): Bus stop sign + bus at the curb. Boy is outside on the sidewalk waving. Driver visible through front window waiting.
            Panel 2 (RESTAURANT): Restaurant table with tonkatsu plate clearly visible. Boy seated smiling, holding chopsticks.
            Panel 3 (HOME DOORWAY): Boy opens front door. Full dog visible wagging and greeting.
            Panel 4 (BEDROOM OVERHEAD): Overhead bedroom view with bed. Boy sits on bed with dog nearby, smiling contentedly.

            Cut Information:
            - Character: {state.storyboard.character_appearance or "A generic person"}
            - Summary: {cut.summary}
            - Emotion: {cut.emotion}
            - Scene: {cut.scene}
            - Dialogue: {cut.dialogue}
            - Camera: {cut.camera}

            Output only the single-line prompt text in English.
            Focus on the visual scene only. Do not include dialogue, speech bubbles, or specific text/captions in the prompt.
            Do not describe the character's appearance in detail. Just refer to them as "the character".
            Keep the prompt concise (max 20 words) to fit within length limits.
            """
        p = invoke_text_model(prompt, temperature=0.3).strip()
        prompts.append(ImagePrompt(cut_index=cut.cut_index, prompt=p))

    state.prompts = prompts
    update_job(state.job_id, prompts=prompts)
    _set_progress(state, 45)
    return state


def generate_images(state: OrchestrationState) -> OrchestrationState:
    _set_progress(state, 60)

    # Convert prompts to dict for easy access
    pmap = {p.cut_index: p.prompt for p in state.prompts}
    
    # Check if we are doing a full generation (Cuts 1-4 present)
    # And if so, try to generate as a single 2x2 grid for consistency
    is_full_batch = all(i in pmap for i in [1, 2, 3, 4])
    
    generated_images: List[CutImage] = []
    
    if is_full_batch:
        print("Generating 4-panel strip for consistency...")
        
        # Sort prompts by index to ensure Cut 1 is generated first
        sorted_prompts = sorted(state.prompts, key=lambda p: p.cut_index)
        
        ref_bytes = None
        
        # Generate individually (or for retries)
        for p in sorted_prompts:
            # If we already generated this cut in grid mode (unlikely here if logic holds), skip
            if any(img.cut_index == p.cut_index for img in generated_images):
                continue
                
            # Prepend character description for individual generation
            char_desc = state.storyboard.character_appearance or "A generic person"
            full_prompt = (
                f"Main character: {char_desc}\n"
                f"Style: {state.style_guide}\n"
                f"{p.prompt}\n"
            )
            #cut_index가 1인 경우에는 ref_image를 profile_image로 설정
            if p.cut_index == 1:
                ref_bytes = state.profile_image

            # Cut 1: Use Profile Image as Reference if available
            if p.cut_index == 1 and state.profile_image:
                 ref_bytes = state.profile_image
            
            # Use ref_image if available (from Cut 1 or previous)
            out = invoke_image_model_to_s3(
                cut_prompt=full_prompt, 
                job_id=state.job_id, 
                cut_index=p.cut_index,
                ref_image=ref_bytes
            )
            
            # If this is Cut 1, save its bytes as reference for subsequent cuts
            if p.cut_index == 1 and out.img_bytes:
                ref_bytes = out.img_bytes
                
            generated_images.append(CutImage(
                cut_index=p.cut_index, 
                image_url=out.url, 
                meta={"source": "bedrock_single", "s3_key": out.s3_key}
            ))

    state.images = generated_images
    update_job(state.job_id, images=generated_images)

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
        # If it's a full 4-panel strip (cut_index=0), skip individual QA for now
        if img.cut_index == 0:
            qa_results.append(QAResult(
                cut_index=0,
                status="PASS",
                reason="Full 4-panel strip generated successfully.",
                fix_hint=None
            ))
            continue

        cut = cut_map[img.cut_index]
        ptxt = prompt_map[img.cut_index]

        qprompt = f"""
            You are a Comic QA Specialist. Check if the prompt matches the cut's intent.
            Judge as PASS or FAIL. If FAIL, provide a short reason and a fix hint.
            Output MUST be in JSON format only.

            Schema:
            {{"status":"PASS"|"FAIL","reason": "...","fix_hint":"..."}}

            Cut Intent:
            - Summary: {cut.summary}
            - Emotion: {cut.emotion}
            - Scene: {cut.scene}
            - Dialogue: {cut.dialogue}
            - Camera: {cut.camera}

            Used Prompt:
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
            You are an Image Prompt Rewriter.
            Keep the original prompt's core but improve it to resolve the QA failure reason.
            Output only the revised single-line prompt text in English.

            Original Prompt:
            {old_prompt}

            QA Failure Reason:
            {r.reason}

            Fix Hint:
            {r.fix_hint}
            """
        new_prompt = invoke_text_model(revise_prompt, temperature=0.25).strip()

        # state 반영
        for p in state.prompts:
            if p.cut_index == r.cut_index:
                p.prompt = new_prompt

        # 이미지 재생성
        # layout="single" (default), ref_image=None (for now)
        out = invoke_image_model_to_s3(
            cut_prompt=new_prompt, 
            job_id=state.job_id, 
            cut_index=r.cut_index
        )
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
