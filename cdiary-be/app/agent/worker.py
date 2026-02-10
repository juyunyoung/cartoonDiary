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
