from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import JobStatus


class SubmittalLineItem(BaseModel):
    title: str = Field(..., description="Name of the required submittal or equipment.")
    category: str = Field(..., description="e.g., 'Product Data', 'Shop Drawings'")
    covered_by_title: bool = False
    has_drawing_match: bool = False
    decision: str = Field(..., description="'Keep', 'Review/Drop', 'Covered by Title'")
    evidence_spec: List[str] = Field(default_factory=list)
    evidence_drawing: List[str] = Field(default_factory=list)


class SubmittalJobResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: Optional[str] = None
    results: Optional[List[SubmittalLineItem]] = None
    csv_download_url: Optional[str] = None
