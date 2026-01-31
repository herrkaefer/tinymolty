from __future__ import annotations

from openai import AsyncOpenAI

from .base import LLMProvider, LLMResponse


class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str, temperature: float) -> None:
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = model
        self.temperature = temperature

    async def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        response = await self.client.chat.completions.create(
            model=self.model,
            temperature=self.temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        content = response.choices[0].message.content or ""
        return LLMResponse(content=content, raw=response)
