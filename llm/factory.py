from __future__ import annotations

from config import LLMConfig

from .base import LLMProvider
from .gemini_provider import GeminiProvider
from .openai_provider import OpenAIProvider
from .openrouter_provider import OpenRouterProvider


def build_provider(config: LLMConfig, api_key: str) -> LLMProvider:
    if config.provider == "openai":
        return OpenAIProvider(api_key=api_key, model=config.model, temperature=config.temperature)
    if config.provider == "openrouter":
        return OpenRouterProvider(api_key=api_key, model=config.model, temperature=config.temperature)
    if config.provider == "gemini":
        return GeminiProvider(api_key=api_key, model=config.model, temperature=config.temperature)
    raise ValueError(f"Unsupported provider: {config.provider}")
