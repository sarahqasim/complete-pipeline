"""
Submittal validator — checks completeness and confidence of results.
"""
from __future__ import annotations

from typing import Any, Dict, List


def validate(job_id: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
    issues: List[str] = []
    confidence = 0.95

    if not results:
        return {"job_id": job_id, "is_valid": False, "confidence_score": 0.0,
                "issues": ["No submittal results produced."]}

    for idx, item in enumerate(results, start=1):
        if not str(item.get("title", "")).strip():
            issues.append(f"Item {idx}: missing title.")
            confidence -= 0.1
        if item.get("has_drawing_match") and not item.get("evidence_drawing"):
            issues.append(f"Item {idx}: flagged as drawing match but no evidence provided.")
            confidence -= 0.05

    return {
        "job_id": job_id,
        "is_valid": len(issues) == 0,
        "confidence_score": round(max(confidence, 0.0), 2),
        "issues": issues,
    }
