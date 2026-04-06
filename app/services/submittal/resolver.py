"""
Submittal resolver — validates candidates against drawing evidence.
Wraps the validation logic from the shared validation service.
"""
from __future__ import annotations

from typing import Any, Dict, List


def resolve(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Apply decision logic: Keep / Review-Drop / Covered by Title."""
    for item in results:
        if item.get("covered_by_title"):
            item["decision"] = "Covered by Title"
        elif not item.get("has_drawing_match"):
            item["decision"] = "Review/Drop"
        else:
            item["decision"] = "Keep"
    return results
