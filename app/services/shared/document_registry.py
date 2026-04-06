"""
Registers uploaded documents and assigns IDs.
Tracks source type (spec / drawing) per job.
"""
from __future__ import annotations

from typing import Dict, List
from pathlib import Path

_registry: Dict[str, Dict[str, List[str]]] = {}


def register(job_id: str, spec_path: Path, drawing_path: Path) -> None:
    _registry[job_id] = {
        "spec": [str(spec_path)],
        "drawing": [str(drawing_path)],
    }


def get_paths(job_id: str) -> Dict[str, List[str]]:
    return _registry.get(job_id, {"spec": [], "drawing": []})
