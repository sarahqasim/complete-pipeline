import json
import re
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd

from app.config import settings
from app.db.session import SessionLocal
from app.models.document import Document
from app.llms import LLMRequest, generate_with_fallback
from app.schemas.submittal import SubmittalLineItem
from app.services.shared.spec.pdf_reader import extract_pdf_text
from app.services.shared.drawing.vision_extractor import extract_drawing_vision

# In-memory job tracking for demo (use Redis/DB in prod)
jobs: Dict[str, Dict[str, Any]] = {}

SYNTHESIS_SYSTEM_PROMPT = """You are an expert mechanical engineering submittal specialist working on a school electrification and heat pump project (P.S. 169, Queens, NY - Design No. D021779).

Your task is to extract all possible submittal line items by:

1) Reading the specification sections:
- For each spec section, navigate directly to the "List of Submittals" section.
- Locate the "Product Data" and "Shop Drawings" subsections.
- Extract every required submittal item listed there (label this set as A).
- Then read the full spec section (Part 1 General, Part 2 Products, Part 3 Execution) to understand full context around A (equipment, components, accessories, installation requirements).

2) Reading the engineering drawings:
- Drawings are the source of truth for what is actually installed and how each item should be named.
- Cross-match every spec submittal item against drawings.
- When matched, use the drawing naming exactly (equipment tags, schedule labels, keynotes, legend callouts), not generic spec wording.

Rules:
- The first line item for every spec section is always the spec section title itself (header row).
- Build "Requirements of list of submittal" from Product Data and Shop Drawings.
- Use full spec body context to correctly identify potential submittal items.
- Prefer drawing designations for final Submittal naming whenever match exists.
- If spec equipment appears in drawings: Match_with_Drawings = true.
- If spec equipment does not appear in drawings: Match_with_Drawings = false.
- SR# is global sequential numbering across all spec sections.
- Ref# is per-section item numbering: header row carries same number as SR#, then sub-items use 1.1, 1.2, 1.3 style.
- Evidence must include sheet number plus specific location/context (schedule row, keynote, symbol, detail label, legend entry).
- For non-matches, set Evidence to "Not found in drawings."

Return ONLY valid JSON array (no markdown, no explanations), using this schema:
[
  {
    "SR#": 1,
    "Design_Number": "Spec Section XXXXX",
    "Ref#": 1,
    "Submittal": "SPEC SECTION TITLE",
    "Match_with_Drawings": true,
    "Evidence": "Sheet [X]: [brief description of where/how this item appears]"
  }
]
"""


def _as_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        val = value.strip().lower()
        if val in {"true", "yes", "1", "y"}:
            return True
        if val in {"false", "no", "0", "n"}:
            return False
    return default


def _as_list_of_str(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v).strip() for v in value if str(v).strip()]
    if isinstance(value, str):
        cleaned = value.strip()
        return [cleaned] if cleaned else []
    return [str(value).strip()] if str(value).strip() else []


def _extract_items_from_llm_payload(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return [x for x in payload if isinstance(x, dict)]
    if not isinstance(payload, dict):
        return []

    for key in ("items", "line_items", "results", "submittals", "data"):
        val = payload.get(key)
        if isinstance(val, list):
            return [x for x in val if isinstance(x, dict)]

    # Fallback: first list value in object
    for val in payload.values():
        if isinstance(val, list):
            return [x for x in val if isinstance(x, dict)]

    return []


def _normalize_item(raw_item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    title = str(
        raw_item.get("title")
        or raw_item.get("name")
        or raw_item.get("what")
        or raw_item.get("submittal")
        or raw_item.get("Submittal")
        or ""
    ).strip()
    if not title:
        return None

    covered_by_title = _as_bool(raw_item.get("covered_by_title"), default=False)
    has_drawing_match = _as_bool(
        raw_item.get("has_drawing_match", raw_item.get("Match_with_Drawings")),
        default=False,
    )

    category = str(raw_item.get("category") or "").strip()
    if not category:
        lower_title = title.lower()
        if lower_title.startswith("product data"):
            category = "Product Data"
        elif lower_title.startswith("shop drawings"):
            category = "Shop Drawings"
        else:
            category = "Other"

    decision = str(raw_item.get("decision") or "").strip()
    if not decision:
        if covered_by_title:
            decision = "Covered by Title"
        elif has_drawing_match:
            decision = "Keep"
        else:
            decision = "Review/Drop"

    evidence_spec = _as_list_of_str(raw_item.get("evidence_spec"))
    evidence_drawing = _as_list_of_str(
        raw_item.get("evidence_drawing", raw_item.get("Evidence"))
    )

    # Support nested evidence object if model returns it that way.
    evidence_obj = raw_item.get("evidence")
    if isinstance(evidence_obj, dict):
        if not evidence_spec:
            evidence_spec = _as_list_of_str(evidence_obj.get("spec"))
        if not evidence_drawing:
            draw_entries = evidence_obj.get("drawings")
            if isinstance(draw_entries, list):
                normalized_drawings: List[str] = []
                for entry in draw_entries:
                    if isinstance(entry, dict):
                        sheet = str(entry.get("sheet", "")).strip()
                        snippet = str(entry.get("snippet", "")).strip()
                        line = f"{sheet}: {snippet}".strip(": ").strip()
                        if line:
                            normalized_drawings.append(line)
                    elif isinstance(entry, str) and entry.strip():
                        normalized_drawings.append(entry.strip())
                evidence_drawing = normalized_drawings
            else:
                evidence_drawing = _as_list_of_str(draw_entries)

    return {
        "title": title,
        "category": category,
        "covered_by_title": covered_by_title,
        "has_drawing_match": has_drawing_match,
        "decision": decision,
        "evidence_spec": evidence_spec,
        "evidence_drawing": evidence_drawing,
    }


def _call_synthesis_model(user_prompt: str) -> str:
    request = LLMRequest(
        system_prompt=SYNTHESIS_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model=settings.TEXT_MODEL,
        temperature=0.2,
        require_json=True,
    )
    return generate_with_fallback(request)


def _persist_submittal_data(
    job_id: str,
    spec_path: Path,
    drawing_path: Path,
    specs_text: str,
    drawings_data: List[Dict[str, Any]],
    results: List[SubmittalLineItem],
) -> None:
    db = SessionLocal()
    try:
        spec_doc = Document(file_name=spec_path.name, file_type="spec", file_hash=job_id)
        drawing_doc = Document(file_name=drawing_path.name, file_type="drawing", file_hash=job_id)
        db.add(spec_doc)
        db.add(drawing_doc)
        db.flush()

        spec_extracted = ExtractedData(
            document_id=spec_doc.id,
            raw_text=specs_text[:1000000],
            extracted_json=json.dumps({"source": "spec_text"}, ensure_ascii=False),
        )
        drawing_extracted = ExtractedData(
            document_id=drawing_doc.id,
            raw_text=None,
            extracted_json=json.dumps(drawings_data, ensure_ascii=False)[:1000000],
        )
        db.add(spec_extracted)
        db.add(drawing_extracted)
        db.flush()

        for item in results:
            item_data = item.model_dump()
            normalized = NormalizedData(
                extracted_id=spec_extracted.id,
                canonical_name=item_data.get("title"),
                normalized_fields=json.dumps(item_data, ensure_ascii=False),
            )
            db.add(normalized)

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


async def process_submittal_job(job_id: str, spec_path: Path, drawing_path: Path):
    """Background task to process the PDFs."""
    jobs[job_id]["status"] = "processing"
    
    try:
        # Step 1: Specs Text Extraction
        specs_data = extract_pdf_text(spec_path)
        specs_text = "\n\n".join([p["text"] for p in specs_data])
        
        # Step 2: Drawings Vision Extraction
        drawings_data = extract_drawing_vision(drawing_path)
        
        # Step 3: Synthesis LLM call (Gemini or OpenAI-compatible)
        user_prompt = f"--- SPECS ---\n{specs_text[:50000]}\n\n--- DRAWINGS DATA ---\n{json.dumps(drawings_data)}"
        raw = _call_synthesis_model(user_prompt)
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)
        
        parsed_payload = json.loads(raw)
        items_json = _extract_items_from_llm_payload(parsed_payload)

        normalized_items: List[Dict[str, Any]] = []
        for item in items_json:
            normalized = _normalize_item(item)
            if normalized:
                normalized_items.append(normalized)

        if not normalized_items:
            raise ValueError(
                "No valid submittal items returned by synthesis model. "
                "Check model output schema or prompt."
            )

        # Parse into Pydantic models after normalization
        results = [SubmittalLineItem(**item) for item in normalized_items]

        # Persist extracted + normalized artifacts for shared downstream use.
        _persist_submittal_data(
            job_id=job_id,
            spec_path=spec_path,
            drawing_path=drawing_path,
            specs_text=specs_text,
            drawings_data=drawings_data,
            results=results,
        )
        
        # Generate Excel
        excel_path = Path(settings.OUTPUT_DIR) / f"{job_id}.xlsx"
        df = pd.DataFrame([iter.model_dump() for iter in results])
        df.to_excel(excel_path, index=False, engine="openpyxl")
        
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["results"] = [r.model_dump() for r in results]
        jobs[job_id]["excel_download_url"] = f"/submittals/download/{job_id}"
        
    except Exception as e:
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["message"] = str(e)

def get_job(job_id: str) -> Dict[str, Any]:
    return jobs.get(job_id)

def create_job() -> str:
    job_id = str(uuid.uuid4())
    jobs[job_id] = {"status": "pending"}
    return job_id
