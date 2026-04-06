"""
Submittal log endpoints.

Flow:
  POST /api/v1/submittals/upload          — upload spec + drawing PDFs
  POST /api/v1/submittals/{job_id}/process — trigger background extraction
  GET  /api/v1/submittals/{job_id}/result  — poll for status / results
  GET  /api/v1/submittals/{job_id}/download — download CSV
  POST /api/v1/submittals/{job_id}/validate — validate completed job
"""
from __future__ import annotations

import traceback
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.schemas.common import ExtractResponse, UploadResponse, ValidationResponse
from app.schemas.submittal import SubmittalJobResponse
from app.services.shared import job_service, storage_service, document_registry
from app.services.submittal import candidate_builder, resolver, validator, output_generator
from app.config import settings

router = APIRouter(prefix="/submittals", tags=["submittals"])


async def _run_submittal_pipeline(job_id: str) -> None:
    job_service.update_job(job_id, status="processing")
    try:
        paths = document_registry.get_paths(job_id)
        spec_path = Path(paths["spec"][0])
        drawing_path = Path(paths["drawing"][0])

        results, raw_rows = await candidate_builder.process_submittal_job_async(
            job_id, spec_path, drawing_path
        )

        csv_path = output_generator.write_csv(
            raw_rows, Path(settings.OUTPUT_DIR) / f"{job_id}_submittal.csv"
        )

        job_service.update_job(
            job_id,
            status="completed",
            results=[r.model_dump() for r in results],
            csv_download_url=f"/api/v1/submittals/{job_id}/download",
        )
    except Exception as exc:
        job_service.fail_job(job_id, str(exc), traceback.format_exc())


@router.post("/upload", response_model=UploadResponse)
async def upload_submittal_documents(
    spec_file: UploadFile = File(...),
    drawing_file: UploadFile = File(...),
):
    job_id = job_service.create_job("submittal")
    spec_path = storage_service.save_upload(spec_file, f"{job_id}_spec.pdf")
    drawing_path = storage_service.save_upload(drawing_file, f"{job_id}_drawing.pdf")
    document_registry.register(job_id, spec_path, drawing_path)
    return UploadResponse(upload_id=job_id, spec_path=str(spec_path), drawing_path=str(drawing_path))


@router.post("/{job_id}/process", response_model=ExtractResponse)
async def process_submittal(job_id: str, background_tasks: BackgroundTasks):
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found. Call /upload first.")
    background_tasks.add_task(_run_submittal_pipeline, job_id)
    return ExtractResponse(job_id=job_id, status="queued")


@router.get("/{job_id}/result", response_model=SubmittalJobResponse)
async def get_submittal_result(job_id: str):
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return SubmittalJobResponse(
        job_id=job_id,
        status=job.get("status", "pending"),
        message=job.get("message"),
        results=job.get("results"),
        csv_download_url=job.get("csv_download_url"),
    )


@router.get("/{job_id}/download")
async def download_submittal_csv(job_id: str):
    csv_path = Path(settings.OUTPUT_DIR) / f"{job_id}_submittal.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="CSV not ready yet.")
    return FileResponse(path=str(csv_path), media_type="text/csv",
                        filename=f"submittal_log_{job_id}.csv")


@router.post("/{job_id}/validate", response_model=ValidationResponse)
async def validate_submittal(job_id: str):
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    return validator.validate(job_id, job.get("results") or [])
