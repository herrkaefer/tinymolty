from __future__ import annotations

import asyncio

from .base import LLMProvider, LLMResponse


class GeminiProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, temperature: float) -> None:
        try:
            from google import genai  # type: ignore
        except Exception as exc:  # pragma: no cover - optional dependency
            raise RuntimeError("google-genai is required for Gemini provider") from exc
        self._genai = genai
        self.client = genai.Client(api_key=api_key)
        self.model = model
        self.temperature = temperature

    async def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        prompt = f"{system_prompt}\n\n{user_prompt}"

        def _call() -> object:
            return self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config={"temperature": self.temperature},
            )

        response = await asyncio.to_thread(_call)
        content = getattr(response, "text", None) or ""
        return LLMResponse(content=content, raw=response)
