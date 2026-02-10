from __future__ import annotations
from typing import Dict, Optional
from threading import Lock
from .models import JobStatus

_jobs: Dict[str, JobStatus] = {}
_lock = Lock()


def create_job(job: JobStatus) -> None:
    with _lock:
        _jobs[job.job_id] = job


def get_job(job_id: str) -> Optional[JobStatus]:
    with _lock:
        return _jobs.get(job_id)


def update_job(job_id: str, **kwargs) -> None:
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return
        # Pydantic v2 `model_copy(update=...)`
        updated = job.model_copy(update=kwargs)
        _jobs[job_id] = updated
