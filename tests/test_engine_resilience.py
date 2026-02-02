import asyncio
import unittest
from unittest.mock import patch

from bot_engine import BotEngine
from config import AppConfig
from llm.base import LLMProvider, LLMResponse
from scheduler import Scheduler
from ui.base import UserInterface


class DummyClient:
    async def get_me(self):
        return {
            "agent": {
                "name": "Test Agent",
                "username": "test",
                "is_claimed": True,
                "karma": 0,
                "stats": {"posts": 0, "comments": 0},
            }
        }


class FakeLLM(LLMProvider):
    async def generate(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        return LLMResponse(content="none")


class CapturingUI(UserInterface):
    def __init__(self) -> None:
        self.status: list[str] = []

    async def start(self) -> None:
        return None

    async def stop(self) -> None:
        return None

    async def send_status(self, message: str) -> None:
        self.status.append(message)

    async def prompt(self, message: str) -> str:
        return "ok"

    async def get_command(self) -> str | None:
        return None

    async def update_activity(self, message: str, next_action_seconds: float | None = None) -> None:
        return None


class BotEngineResilienceTests(unittest.TestCase):
    def test_run_loop_recovers_from_tick_exception(self) -> None:
        config = AppConfig()
        ui = CapturingUI()
        scheduler = Scheduler(config.behavior, config.advanced)
        engine = BotEngine(
            config=config,
            client=DummyClient(),
            llm=FakeLLM(),
            scheduler=scheduler,
            ui=ui,
        )

        call_count = 0

        async def boom_then_stop():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("boom")
            engine._running = False

        engine._tick = boom_then_stop  # type: ignore[method-assign]

        async def fast_sleep(*args, **kwargs):
            return None

        with patch("bot_engine.asyncio.sleep", new=fast_sleep):
            asyncio.run(engine.run_loop())

        self.assertGreaterEqual(call_count, 2)
        self.assertTrue(any("Engine loop error" in msg for msg in ui.status))

    def test_quit_command_stops_engine(self) -> None:
        config = AppConfig()
        ui = CapturingUI()
        scheduler = Scheduler(config.behavior, config.advanced)
        engine = BotEngine(
            config=config,
            client=DummyClient(),
            llm=FakeLLM(),
            scheduler=scheduler,
            ui=ui,
        )
        engine._running = True

        async def _run():
            await engine.handle_command("/quit")

        asyncio.run(_run())
        self.assertFalse(engine._running)

