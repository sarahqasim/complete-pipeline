from dataclasses import dataclass
from typing import Protocol


@dataclass
class LLMRequest:
    system_prompt: str
    user_prompt: str
    model: str
    temperature: float = 0.2
    require_json: bool = True


class TextLLM(Protocol):
    def generate(self, request: LLMRequest) -> str:
        ...

