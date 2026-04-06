"""
Abstracts file storage. Currently local disk — swap out for S3/Azure later
without touching any other service.
"""
from __future__ import annotations

import shutil
from pathlib import Path
from fastapi import UploadFile
from app.config import settings


def save_upload(file: UploadFile, filename: str) -> Path:
    dest = Path(settings.UPLOAD_DIR) / filename
    dest.parent.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as buf:
        shutil.copyfileobj(file.file, buf)
    return dest


def output_path(filename: str) -> Path:
    path = Path(settings.OUTPUT_DIR) / filename
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def upload_path(filename: str) -> Path:
    return Path(settings.UPLOAD_DIR) / filename
