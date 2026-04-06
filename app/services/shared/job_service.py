"""
Shared in-memory job tracker used by both submittal and equipment pipelines.
Keys are UUID job IDs. Values are dicts with status, results, and metadata.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

_jobs: Dict[str, Dict[str, Any]] = {}


def create_job(job_type: str) -> str:
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {"status": "pending", "job_type": job_type}
    return job_id


def get_job(job_id: str) -> Optional[Dict[str, Any]]:
    return _jobs.get(job_id)


def update_job(job_id: str, **kwargs: Any) -> None:
    if job_id in _jobs:
        _jobs[job_id].update(kwargs)


def fail_job(job_id: str, error: str, tb: str = "") -> None:
    update_job(job_id, status="failed", message=error, traceback=tb)
