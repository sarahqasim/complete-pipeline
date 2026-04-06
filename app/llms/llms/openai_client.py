from openai import BadRequestError, OpenAI

from app.core.config import settings
from app.llms.base import LLMRequest, TextLLM


class OpenAITextLLM(TextLLM):
    def __init__(self) -> None:
        self._client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_BASE_URL)

    def generate(self, request: LLMRequest) -> str:
        try:
            response = self._client.chat.completions.create(
                model=request.model,
                messages=[
                    {"role": "system", "content": request.system_prompt},
                    {"role": "user", "content": request.user_prompt},
                ],
                response_format={"type": "json_object"} if request.require_json and "gpt" in request.model else None,
                temperature=request.temperature,
            )
        except BadRequestError as e:
            raise ValueError(
                f"OpenAI request failed for model '{request.model}' "
                f"with base_url '{settings.OPENAI_BASE_URL or 'default-openai'}': {e}"
            ) from e
        return response.choices[0].message.content or "[]"


