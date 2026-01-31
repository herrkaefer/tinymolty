from __future__ import annotations

import asyncio

from bot_engine import BotEngine
from config import AppConfig, ResolvedSecrets
from llm.factory import build_provider
from moltbook.client import MoltbookClient
from scheduler import Scheduler
from ui.terminal import TerminalUI
from ui.telegram_ui import TelegramUI


def build_ui(config: AppConfig, secrets: ResolvedSecrets):
    if config.ui.mode == "telegram":
        if not secrets.telegram_token:
            raise ValueError("Telegram token is required for telegram UI")
        return TelegramUI(secrets.telegram_token, config.telegram.chat_id)
    return TerminalUI()


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
