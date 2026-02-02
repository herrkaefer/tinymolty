from __future__ import annotations

from config import AppConfig, ResolvedSecrets
from ui.tui_app import TinyMoltyApp, _TextualUIAdapter
from ui.telegram_ui import TelegramUI
from ui.multi import MultiUI


def build_ui(config: AppConfig, secrets: ResolvedSecrets):
    # Check if Telegram is enabled
    if config.telegram.enabled and secrets.telegram_token:
        print("[App] 🔧 Telegram enabled, setting up MultiUI...")
        # For TUI with Telegram: use TinyMoltyApp directly, which will integrate Telegram UI
        return TinyMoltyApp(config, secrets)
    else:
        print("[App] 🖥️  Running in TUI-only mode")
        return TinyMoltyApp(config, secrets)


def run_app(config: AppConfig, secrets: ResolvedSecrets) -> None:
    # Textual owns the event loop; run() blocks until app exits.
    app = build_ui(config, secrets)
    app.run()


def run(config: AppConfig, secrets: ResolvedSecrets) -> None:
    run_app(config, secrets)
