"""
Parses raw text out of spec PDFs into lines.
Used by entity_extractor and can be used independently for chunking.
"""
from __future__ import annotations

from pathlib import Path
from pypdf import PdfReader


def extract_lines(pdf_path: str | Path) -> list[str]:
    reader = PdfReader(pdf_path)
    lines: list[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if not text:
            continue
        for line in text.splitlines():
            clean = line.strip()
            if clean:
                lines.append(clean)
    return lines


def extract_text(pdf_path: str | Path) -> str:
    return "\n".join(extract_lines(pdf_path))
