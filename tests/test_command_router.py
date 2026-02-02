import asyncio
import unittest

from command_router import CommandRouter
from llm.base import LLMProvider, LLMResponse


class WhitespaceLLM(LLMProvider):
    async def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        return LLMResponse(content="  \n\t  ")


class CommandRouterTests(unittest.TestCase):
    def test_llm_whitespace_does_not_crash(self) -> None:
        router = CommandRouter(WhitespaceLLM())

        async def _run():
            return await router.parse("not a slash command")

        result = asyncio.run(_run())
        self.assertEqual(result.source, "llm")
        self.assertEqual(result.command, "none")

