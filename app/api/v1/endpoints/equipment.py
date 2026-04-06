"""
Equipment log endpoints.

Flow:
  POST /api/v1/equipment/upload          — upload spec + drawing PDFs, get upload_id
  POST /api/v1/equipment/{job_id}/process — trigger async extraction
  GET  /api/v1/equipment/{job_id}/result  — poll status / get results
  GET  /api/v1/equipment/{job_id}/download — download combined CSV
"""
from __future__ import annotations

import traceback
from pathlib import Path

from fastapi import APIRouter, BackgroundTasks, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.schemas.common import ExtractResponse, UploadResponse
from app.schemas.equipment import EquipmentJobResponse
from app.services.shared import job_service, storage_service, document_registry
from app.services.equipment import candidate_builder, resolver, output_generator
from app.config import settings

router = APIRouter(prefix="/equipment", tags=["equipment"])


async def _run_equipment_pipeline(job_id: str) -> None:
    job_service.update_job(job_id, status="processing")
    try:
        paths = document_registry.get_paths(job_id)
        spec_paths = [Path(p) for p in paths["spec"]]
        drawing_paths = [Path(p) for p in paths["drawing"]]

        candidates = candidate_builder.build_candidates(drawing_paths)
        resolved = resolver.resolve(candidates, spec_paths)

        if not resolved:
            raise ValueError("No equipment rows produced. Check uploaded PDFs.")

        csv_path = output_generator.write_csv(
            resolved, Path(settings.OUTPUT_DIR) / f"{job_id}_equipment.csv"
        )

        matched = sum(1 for r in resolved if r["status"] == "matched")
        job_service.update_job(
            job_id,
            status="completed",
            total_rows=len(resolved),
            matched_rows=matched,
            results=resolved,
            csv_download_url=f"/api/v1/equipment/{job_id}/download",
        )
    except Exception as exc:
        job_service.fail_job(job_id, str(exc), traceback.format_exc())


@router.post("/upload", response_model=UploadResponse)
async def upload_equipment_documents(
    spec_file: UploadFile = File(...),
    drawing_file: UploadFile = File(...),
):
    job_id = job_service.create_job("equipment")
    spec_path = storage_service.save_upload(spec_file, f"{job_id}_eq_spec.pdf")
    drawing_path = storage_service.save_upload(drawing_file, f"{job_id}_eq_drawing.pdf")
    document_registry.register(job_id, spec_path, drawing_path)
    return UploadResponse(upload_id=job_id, spec_path=str(spec_path), drawing_path=str(drawing_path))


@router.post("/{job_id}/process", response_model=ExtractResponse)
async def process_equipment(job_id: str, background_tasks: BackgroundTasks):
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found. Call /upload first.")
    background_tasks.add_task(_run_equipment_pipeline, job_id)
    return ExtractResponse(job_id=job_id, status="queued")


@router.get("/{job_id}/result", response_model=EquipmentJobResponse)
async def get_equipment_result(job_id: str):
    job = job_service.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    msg = job.get("message", "")
    if job.get("traceback"):
        msg = f"{msg}\n\nTRACEBACK:\n{job['traceback']}"
    return EquipmentJobResponse(
        job_id=job_id,
        status=job.get("status", "pending"),
        message=msg or None,
        total_rows=job.get("total_rows", 0),
        matched_rows=job.get("matched_rows", 0),
        results=job.get("results"),
        csv_download_url=job.get("csv_download_url"),
    )


@router.get("/{job_id}/download")
async def download_equipment_csv(job_id: str):
    csv_path = Path(settings.OUTPUT_DIR) / f"{job_id}_equipment.csv"
    if not csv_path.exists():
        raise HTTPException(status_code=404, detail="CSV not ready yet.")
    return FileResponse(path=str(csv_path), media_type="text/csv",
                        filename=f"equipment_log_{job_id}.csv")
