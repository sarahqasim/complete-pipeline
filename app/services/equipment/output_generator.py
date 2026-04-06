"""
Equipment output generator — writes the final equipment log CSV.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import List

_FIELDS = [
    "equipment_name", "item_detail", "qty", "location_service",
    "electrical", "basis_of_design", "manufacturers", "warranty",
    "training", "spare_parts", "match_score", "status",
]


def write_csv(rows: List[dict], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    return path
