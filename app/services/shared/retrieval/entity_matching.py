"""
Fuzzy keyword-based matching of drawing rows against spec equipment names.
Uses Jaccard similarity on meaningful keywords (stop-words removed).
"""
from __future__ import annotations

import re
from typing import List, Optional

_STOP_WORDS = {
    "the", "a", "an", "of", "and", "or", "for", "to", "in", "at",
    "by", "with", "type", "unit", "schedule", "system",
}

MATCH_THRESHOLD = 0.45


def _keywords(text: str) -> set:
    normalised = re.sub(r"[^a-z0-9\s]", " ", text.lower()).strip()
    return {w for w in normalised.split() if w not in _STOP_WORDS and len(w) > 1}


def _jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def score(draw_row: dict, spec_name: str) -> float:
    """Score one drawing row against a spec equipment name."""
    spec_kw = _keywords(spec_name)
    detail_score = _jaccard(_keywords(str(draw_row.get("item_detail", ""))), spec_kw)
    tag_score = _jaccard(_keywords(str(draw_row.get("equipment_name", ""))), spec_kw) * 0.4
    return max(detail_score, tag_score)


def match_drawing_to_spec(
    draw_row: dict,
    spec_rows: List[dict],
    threshold: float = MATCH_THRESHOLD,
) -> Optional[dict]:
    """Return the best-matching spec row for a drawing row, or None if below threshold."""
    best_row, best_score = None, 0.0
    for spec in spec_rows:
        s = score(draw_row, spec.get("equipment_name", ""))
        if s > best_score:
            best_score, best_row = s, spec
    return best_row if best_score >= threshold else None
