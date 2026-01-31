from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class LLMResponse:
    content: str
    raw: object | None = None


class LLMProvider(ABC):
    @abstractmethod
    async def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        raise NotImplementedError
