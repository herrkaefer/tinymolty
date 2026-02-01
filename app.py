from __future__ import annotations

import asyncio

from bot_engine import BotEngine
from config import AppConfig, ResolvedSecrets, save_config
from llm.factory import build_provider
from moltbook.client import MoltbookClient
from scheduler import Scheduler
from ui.terminal import TerminalUI
from ui.telegram_ui import TelegramUI
from ui.multi import FilteredUI, MultiUI


def _telegram_filter(enabled_actions: list[str]):
    action_keywords = {
        "post": ["post", "posted", "publishing", "generating post"],
        "comment": ["comment", "commented"],
        "upvote": ["upvote", "upvoted"],
        "follow": ["follow", "following"],
        "browse": ["browse", "feed", "fetched"],
        "heartbeat": ["heartbeat"],
    }
    enabled = set(enabled_actions)

    def should_send(message: str) -> bool:
        lowered = message.lower()
        if "tinymolty started" in lowered:
            return True
        if "❌" in message or "⚠️" in message or "error" in lowered or "failed" in lowered:
            return True
        for action in enabled:
            for keyword in action_keywords.get(action, []):
                if keyword in lowered:
                    return True
        return False

    return should_send


def build_ui(config: AppConfig, secrets: ResolvedSecrets):
    terminal = TerminalUI()
    telegram: TelegramUI | None = None
    if config.telegram.enabled:
        if not secrets.telegram_token:
            raise ValueError("Telegram token is required for telegram UI")
        async def on_chat_id(chat_id: str) -> None:
            config.telegram.chat_id = chat_id
            save_config(config)
            await terminal.send_status(f"📨 Telegram chat linked: {chat_id}")

        telegram = FilteredUI(
            TelegramUI(secrets.telegram_token, config.telegram.chat_id, on_chat_id=on_chat_id),
            _telegram_filter(config.behavior.enabled_actions),
        )
    if telegram:
        return MultiUI(terminal, telegram)
    return terminal


async def run_app(config: AppConfig, secrets: ResolvedSecrets) -> None:
    if not secrets.llm_api_key:
        raise ValueError("LLM API key is required")
    ui = build_ui(config, secrets)
    client = MoltbookClient(config.moltbook.credentials_path)
    scheduler = Scheduler(config.behavior, config.advanced)
    llm = build_provider(config.llm, secrets.llm_api_key)
    engine = BotEngine(config, client, llm, scheduler, ui)
    try:
        await engine.run()
    finally:
        await client.close()


def run(config: AppConfig, secrets: ResolvedSecrets) -> None:
    asyncio.run(run_app(config, secrets))
