"""
Equipment resolver — enriches drawing rows with spec data.
For each drawing candidate, finds the best spec match and appends
manufacturers, warranty, training, and spare parts.
"""
from __future__ import annotations

from typing import List

from app.services.shared.spec.entity_extractor import process_pdfs as extract_specs
from app.services.shared.retrieval.entity_matching import match_drawing_to_spec
from pathlib import Path


def resolve(drawing_rows: List[dict], spec_paths: List[Path]) -> List[dict]:
    """Left-join drawing rows with spec enrichment data."""
    spec_rows = extract_specs([str(p) for p in spec_paths])

    resolved = []
    for dr in drawing_rows:
        spec = match_drawing_to_spec(dr, spec_rows)
        row = {
            "equipment_name":   dr.get("equipment_name", ""),
            "item_detail":      dr.get("item_detail", ""),
            "qty":              dr.get("qty", ""),
            "location_service": dr.get("location_service", ""),
            "electrical":       dr.get("electrical", ""),
            "basis_of_design":  dr.get("basis_of_design", ""),
            "manufacturers":    spec.get("manufacturers", "") if spec else "",
            "warranty":         spec.get("warranty", "")      if spec else "",
            "training":         spec.get("training", "")      if spec else "",
            "spare_parts":      spec.get("spare_parts", "")   if spec else "",
            "match_score":      round(
                __import__("app.services.shared.retrieval.entity_matching", fromlist=["score"])
                .score(dr, spec.get("equipment_name", "") if spec else ""), 3
            ),
            "status": "matched" if spec else "unmatched",
        }
        resolved.append(row)
    return resolved
