from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from llm.base import LLMProvider

Command = Literal["pause", "resume", "status", "quit", "help", "none"]
Source = Literal["slash", "llm", "empty"]


@dataclass(slots=True)
class CommandParseResult:
    command: Command
    source: Source
    raw: str
    error: str | None = None


class CommandRouter:
    def __init__(self, llm: LLMProvider) -> None:
        self.llm = llm

    async def parse(self, raw: str) -> CommandParseResult:
        text = raw.strip()
        if not text:
            return CommandParseResult(command="none", source="empty", raw=raw)
        if text.startswith("/"):
            command = text.lstrip("/").split()[0].lower()
            alias_map = {
                "exit": "quit",
                "stop": "quit",
                "start": "resume",
            }
            command = alias_map.get(command, command)
            return CommandParseResult(
                command=command if command in self._allowed() else "none",
                source="slash",
                raw=raw,
            )
        return await self._interpret(text, raw)

    async def _interpret(self, text: str, raw: str) -> CommandParseResult:
        system_prompt = (
            "You are a command router for TinyMolty. "
            "Return only one word from: pause, resume, status, quit, help, none. "
            "Choose none if the input is not a command."
        )
        user_prompt = f"User input: {text}\nCommand:"
        try:
            response = await self.llm.generate(system_prompt, user_prompt)
        except Exception as exc:
            return CommandParseResult(
                command="none",
                source="llm",
                raw=raw,
                error=f"{type(exc).__name__}",
            )
        tokens = response.content.strip().lower().split() if response.content else []
        command = tokens[0] if tokens else "none"
        return CommandParseResult(
            command=command if command in self._allowed() else "none",
            source="llm",
            raw=raw,
        )

    @staticmethod
    def _allowed() -> set[str]:
        return {"pause", "resume", "status", "quit", "help", "none"}
