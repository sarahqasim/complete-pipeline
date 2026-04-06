from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import JobStatus


class MatchStatus(str, Enum):
    matched = "matched"
    unmatched = "unmatched"
    needs_review = "needs_review"


class EquipmentRow(BaseModel):
    equipment_name: str
    item_detail: str = ""
    qty: str = ""
    location_service: str = ""
    electrical: str = ""
    basis_of_design: str = ""
    manufacturers: str = ""
    warranty: str = ""
    training: str = ""
    spare_parts: str = ""
    match_score: float = Field(0.0, description="Spec-drawing match confidence (0–1).")
    status: MatchStatus = MatchStatus.unmatched


class EquipmentJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: Optional[str] = None
    total_rows: int = 0
    matched_rows: int = 0
    results: Optional[List[EquipmentRow]] = None
    csv_download_url: Optional[str] = None
