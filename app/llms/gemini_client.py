import google.genai as genai
from google.genai import types

from app.core.config import settings
from app.llms.base import LLMRequest, TextLLM


class GeminiTextLLM(TextLLM):
    def __init__(self) -> None:
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is required for Gemini text synthesis.")
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def generate(self, request: LLMRequest) -> str:
        response = self._client.models.generate_content(
            model=request.model,
            contents=request.user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=request.system_prompt,
                response_mime_type="application/json" if request.require_json else "text/plain",
                temperature=request.temperature,
            ),
        )
        return response.text or "[]"

