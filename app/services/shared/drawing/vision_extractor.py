import io
import re
import json
from pathlib import Path
from typing import Any, List, Dict
import google.genai as genai
from google.genai import types

from app.config import settings

# ── SYSTEM PROMPT ───────────────────────────────────────────────────

VISION_SYSTEM_PROMPT = """You are an expert mechanical engineer reading construction drawing pages.
You are looking at an IMAGE of the actual drawing — you can see everything: 
diagrams, schedules, tables, labels, dimensions, equipment, ductwork, piping, notes.

TASK: Extract EVERYTHING you can see on this page. Be thorough and complete.
Report every piece of information visible on the page, paying special attention to schedules, tables, and equipment tagging.

OUTPUT FORMAT: Return ONLY valid JSON exactly matching this schema:
{
  "page_type": "string (schedule/floor_plan/detail/diagram/notes/title_sheet)",
  "items": [
    {
      "what": "string (e.g. AHU-1, Exhaust Fan, Valve)",
      "details": "string (all details, specs, values, HP, CFM)",
      "raw_text": "string (text as shown on the drawing)"
    }
  ],
  "tables": [
    {
      "table_name": "string",
      "headers": ["string"],
      "rows": [["string"]]
    }
  ],
  "notes": ["string"]
}
Do not include markdown fences. Only valid JSON.
"""

def pdf_to_images(pdf_path: Path, dpi: int = 200) -> List[Any]:
    """Rasterizes a PDF into images using poppler. Good for visual drawings."""
    from pdf2image import convert_from_path
    
    images = convert_from_path(
        str(pdf_path), 
        dpi=dpi, 
        poppler_path=settings.POPPLER_PATH
    )
    return images

def send_image_to_gemini(api_key: str, pil_image: Any, page_num: int, model: str) -> Dict[str, Any]:
    """Send image directly to Gemini using the google-genai SDK."""
    client = genai.Client(api_key=api_key)

    try:
        response = client.models.generate_content(
            model=model,
            contents=[
                pil_image,
                f"This is page {page_num} of an engineering drawing. Extract everything visible. Return JSON only."
            ],
            config=types.GenerateContentConfig(
                system_instruction=VISION_SYSTEM_PROMPT,
                response_mime_type="application/json",
                temperature=0.2, # Low temp for deterministic extraction
            )
        )
        
        raw = response.text or ""
        raw = re.sub(r"^```(?:json)?\s*", "", raw.strip(), flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw)

        result = json.loads(raw.strip())
        result["page"] = page_num
        return result
        
    except Exception as e:
        return {"page": page_num, "error": str(e)}

def extract_drawing_vision(pdf_path: Path) -> List[Dict[str, Any]]:
    """Process a full drawing PDF by turning it into images and running vision inference."""
    images = pdf_to_images(pdf_path, dpi=settings.DPI_FOR_VISION)
    
    results = []
    # Send each page sequentially (in a real app, thread this or async it)
    for i, img in enumerate(images, start=1):
        res = send_image_to_gemini(
            api_key=settings.GEMINI_API_KEY, 
            pil_image=img, 
            page_num=i, 
            model=settings.VISION_MODEL
        )
        results.append(res)
        
    return results
