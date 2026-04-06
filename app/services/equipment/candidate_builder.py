"""
Equipment candidate builder — drawing-first.
Calls the shared drawing schedule extractor to produce base equipment rows.
"""
from __future__ import annotations

from pathlib import Path
from typing import List

from app.services.shared.drawing.schedule_extractor import process_pdfs


def build_candidates(drawing_paths: List[Path]) -> List[dict]:
    """Extract all equipment rows from drawing PDFs."""
    return process_pdfs([str(p) for p in drawing_paths])
