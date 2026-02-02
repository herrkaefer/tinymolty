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
    response: str | None = None  # Natural language response from LLM


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
            "You are TinyMolty, a friendly AI agent on Moltbook. "
            "First, check if the user wants to execute a command: pause, resume, status, quit, help. "
            "If yes, respond with ONLY that command word. "
            "If no, respond naturally in 1-2 friendly sentences.\n\n"
            "Examples:\n"
            "User: 'what are you doing?' -> 'I'm browsing Moltbook, posting, and commenting on interesting content!'\n"
            "User: 'pause' -> 'pause'\n"
            "User: 'can you stop?' -> 'pause'\n"
            "User: 'tell me your status' -> 'status'"
        )
        user_prompt = f"User: {text}"
        try:
            response = await self.llm.generate(system_prompt, user_prompt)
        except Exception as exc:
            return CommandParseResult(
                command="none",
                source="llm",
                raw=raw,
                error=f"{type(exc).__name__}",
                response="Sorry, I couldn't process that right now.",
            )

        content = response.content.strip() if response.content else ""
        tokens = content.lower().split()
        first_word = tokens[0] if tokens else "none"

        # Check if response is a single command word
        if first_word in self._allowed() and len(tokens) == 1:
            return CommandParseResult(
                command=first_word,
                source="llm",
                raw=raw,
            )

        # Otherwise, treat as natural language response
        return CommandParseResult(
            command="none",
            source="llm",
            raw=raw,
            response=content,
        )

    @staticmethod
    def _allowed() -> set[str]:
        return {"pause", "resume", "status", "quit", "help", "none"}
