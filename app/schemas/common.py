from enum import Enum
from pydantic import BaseModel


class JobStatus(str, Enum):
    pending = "pending"
    processing = "processing"
    completed = "completed"
    failed = "failed"


class HealthResponse(BaseModel):
    status: str
    version: str


class UploadResponse(BaseModel):
    upload_id: str
    spec_path: str
    drawing_path: str


class ExtractResponse(BaseModel):
    job_id: str
    status: str


class ValidationResponse(BaseModel):
    job_id: str
    is_valid: bool
    confidence_score: float
    issues: list[str]
