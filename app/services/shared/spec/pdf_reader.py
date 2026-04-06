import re
from pathlib import Path
from typing import Any, List, Dict

def guess_sheet_id(text: str, file_name: str, page_num: int) -> str:
    """Detect sheet ID like M301, M401, E201 from text. Adapted from spec_to_submittals.py"""
    m = re.search(r"\b([A-Z]{1,2}\d{2,4}(?:\.\d+)?)\b", text)
    if m:
        return m.group(1)
    m = re.search(r"\b([MPEA]\s*[-]?\s*\d{2,4})\b", text, flags=re.IGNORECASE)
    if m:
        return re.sub(r"\s+", "", m.group(1)).upper()
    stem = Path(file_name).stem
    return f"{stem}-P{page_num}"

def extract_pdf_text(pdf_path: Path) -> List[Dict[str, Any]]:
    """Extract all text from a PDF, which is cheap and perfect for text-dense Specs."""
    try:
        from pypdf import PdfReader
    except ImportError:
        return []

    reader = PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = page.extract_text() or ""
        text = re.sub(r"\s+", " ", text).strip()
        pages.append({
            "page": i,
            "sheet_id": guess_sheet_id(text, pdf_path.name, i),
            "text": text,
        })
    return pages
