import time
from typing import Optional

from app.core.config import settings
from app.llms.base import LLMRequest, TextLLM
from app.llms.gemini_client import GeminiTextLLM
from app.llms.openai_client import OpenAITextLLM


def _get_text_llm_by_provider(provider: str, model: str) -> TextLLM:
    normalized_provider = (provider or "auto").strip().lower()
    normalized_model = (model or "").strip().lower()

    if normalized_provider == "gemini" or normalized_model.startswith("gemini"):
        return GeminiTextLLM()
    if normalized_provider == "openai":
        return OpenAITextLLM()

    # auto mode
    if settings.OPENAI_API_KEY:
        return OpenAITextLLM()
    if settings.GEMINI_API_KEY:
        return GeminiTextLLM()
    raise ValueError("No LLM credentials configured. Set OPENAI_API_KEY or GEMINI_API_KEY.")


def get_text_llm() -> TextLLM:
    return _get_text_llm_by_provider(settings.LLM_PROVIDER, settings.TEXT_MODEL)


def generate_with_fallback(request: LLMRequest) -> str:
    primary_llm = _get_text_llm_by_provider(settings.LLM_PROVIDER, request.model)
    max_retries = max(1, settings.LLM_MAX_RETRIES)
    retry_delay = max(0.0, settings.LLM_RETRY_DELAY_SECONDS)

    primary_error: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            return primary_llm.generate(request)
        except Exception as e:
            primary_error = e
            if attempt < max_retries - 1 and retry_delay > 0:
                time.sleep(retry_delay)

    fallback_model = (settings.FALLBACK_TEXT_MODEL or "").strip()
    fallback_provider = (settings.LLM_FALLBACK_PROVIDER or "").strip()
    if fallback_model:
        fallback_llm = _get_text_llm_by_provider(
            fallback_provider if fallback_provider else "auto",
            fallback_model,
        )
        fallback_request = LLMRequest(
            system_prompt=request.system_prompt,
            user_prompt=request.user_prompt,
            model=fallback_model,
            temperature=request.temperature,
            require_json=request.require_json,
        )
        return fallback_llm.generate(fallback_request)

    if primary_error:
        raise primary_error
    raise ValueError("LLM request failed with no fallback configured.")

