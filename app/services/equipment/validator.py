"""
Equipment validator — checks completeness of resolved rows.
Flags rows missing key fields or with low match scores.
"""
from __future__ import annotations

from typing import List


def validate(rows: List[dict]) -> List[dict]:
    for row in rows:
        issues = []
        if not row.get("equipment_name"):
            issues.append("missing_tag")
        if not row.get("manufacturers") and row.get("status") == "matched":
            issues.append("missing_manufacturer")
        if row.get("match_score", 0) < 0.3 and row.get("status") == "matched":
            issues.append("low_confidence")
        if issues:
            row["status"] = "needs_review"
            row["validation_notes"] = ", ".join(issues)
    return rows
