import asyncio
import unittest

from bot_engine import BotEngine
from config import AppConfig
from llm.base import LLMProvider, LLMResponse
from moltbook.models import Post
from scheduler import Scheduler
from ui.base import UserInterface


class FakeLLM(LLMProvider):
    async def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        return LLMResponse(
            content='[{"id": "b", "score": 0.9}, {"id": "a", "score": 0.1}]'
        )


class DummyUI(UserInterface):
    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    async def send_status(self, message: str) -> None:
        return None

    async def prompt(self, message: str) -> str:
        return "ok"

    async def get_command(self) -> str | None:
        return None

    async def update_activity(self, message: str, next_action_seconds: float | None = None) -> None:
        return None


class BotEngineTests(unittest.TestCase):
    def test_score_posts_orders_by_llm(self):
        config = AppConfig()
        scheduler = Scheduler(config.behavior, config.advanced)
        engine = BotEngine(
            config=config,
            client=object(),
            llm=FakeLLM(),
            scheduler=scheduler,
            ui=DummyUI(),
        )
        posts = [Post(id="a", content="A"), Post(id="b", content="B")]

        async def _run():
            ranked = await engine._score_posts(posts)
            return [post.id for post in ranked]

        ranked_ids = asyncio.run(_run())
        self.assertEqual(ranked_ids, ["b", "a"])
