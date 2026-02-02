from __future__ import annotations

from config import AppConfig, ResolvedSecrets
from ui.tui_app import TinyMoltyApp


def build_ui(config: AppConfig, secrets: ResolvedSecrets):
    return TinyMoltyApp(config, secrets)


def run_app(config: AppConfig, secrets: ResolvedSecrets) -> None:
    # Textual owns the event loop; run() blocks until app exits.
    app = build_ui(config, secrets)
    app.run()


def run(config: AppConfig, secrets: ResolvedSecrets) -> None:
    run_app(config, secrets)
