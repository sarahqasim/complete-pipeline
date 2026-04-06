"""
Submittal output generator — writes the final submittal log as CSV.
(Previously output as XLSX; both features now output CSV per project rules.)
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List

_FIELDS = [
    "SR#", "Design_Number", "Ref#", "Submittal",
    "Match_with_Drawings", "Evidence", "decision",
]


def write_csv(rows: List[Dict[str, Any]], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path
