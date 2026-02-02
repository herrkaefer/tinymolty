from __future__ import annotations

import asyncio
from datetime import datetime

from rich.text import Text
from textual import on
from textual.app import App, ComposeResult
from textual.message import Message
from textual.worker import Worker, WorkerState
from textual.widgets import Input, Log, Static

from bot_engine import BotEngine
from config import AppConfig, ResolvedSecrets
from llm.factory import build_provider
from moltbook.client import MoltbookClient
from scheduler import Scheduler
from ui.telegram_ui import TelegramUI
from ui.multi import MultiUI


class StatusMessage(Message):
    def __init__(self, text: str) -> None:
        super().__init__()
        self.text = text


class QuitRequest(Message):
    pass


class _UILog(Log):
    can_focus = False
    can_focus_children = False


class _TextualUIAdapter:
    """Minimal UI adapter used by BotEngine.

    Best practice in Textual is to update UI via messages from background work.
    """

    def __init__(self, app: "TinyMoltyApp") -> None:
        self.app = app

    async def start(self) -> None:  # matches UserInterface shape
        return

    async def stop(self) -> None:  # matches UserInterface shape
        return

    async def send_status(self, message: str) -> None:
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.app.post_message(StatusMessage(f"[{timestamp}] {message}"))

    async def prompt(self, message: str) -> str:
        # Not used in the runtime loop currently.
        await self.send_status(message)
        return ""

    async def get_command(self) -> str | None:
        # Commands are handled directly by the TUI, not pulled by the engine.
        return None

    async def update_activity(self, message: str, next_action_seconds: float | None = None) -> None:
        # For now we don't render activity in the header (keeps UI stable and uncluttered).
        return

    def set_agent_info(
        self,
        agent_name: str,
        profile_url: str | None,
        owner_name: str = "",
    ) -> None:
        self.app.set_agent_info(agent_name, profile_url, owner_name)


class TinyMoltyApp(App):
    CSS = """
    Screen {
        padding: 1;
    }
    #header {
        height: 3;
        margin-bottom: 1;
    }
    #log {
        height: 1fr;
        border: solid $accent;
    }
    #command {
        height: 3;
        margin-top: 1;
    }
    """

    def __init__(self, config: AppConfig, secrets: ResolvedSecrets) -> None:
        super().__init__()
        self.config = config
        self.secrets = secrets
        self._engine: BotEngine | None = None
        self._client: MoltbookClient | None = None
        self._command_queue: asyncio.Queue[str] = asyncio.Queue()

    def compose(self) -> ComposeResult:
        yield Static("Agent: (loading...)", id="header")
        yield _UILog(id="log")
        yield Input(
            placeholder="Type /pause /resume /status /quit /help or use natural language",
            id="command",
        )

    async def on_mount(self) -> None:
        self.query_one(Input).focus()
        # Run bot loop and command handling as workers so the UI stays responsive.
        # Note: exclusive workers cancel other workers in the same group; avoid for long-lived loops.
        self.run_worker(self._run_engine(), name="engine", group="engine")
        self.run_worker(self._command_loop(), name="commands", group="commands")

    async def on_unmount(self) -> None:
        if self._client:
            await self._client.close()

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        worker = event.worker
        if worker.state != WorkerState.ERROR:
            return

        error = getattr(worker, "error", None)
        error_text = f"{type(error).__name__}: {error}" if error else "Unknown error"

        if worker.name == "commands":
            self.post_message(
                StatusMessage(
                    f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Command worker crashed; restarting. ({error_text[:200]})"
                )
            )
            self.run_worker(self._command_loop(), name="commands", group="commands")
            return

        if worker.name == "engine":
            self.post_message(
                StatusMessage(
                    f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Engine worker crashed; please restart the app. ({error_text[:200]})"
                )
            )

    @on(StatusMessage)
    def _on_status(self, message: StatusMessage) -> None:
        # Log.write_line expects a string, but Log.wrap=True handles wrapping
        self.query_one(_UILog).write_line(message.text)

    @on(Input.Submitted)
    def _on_input_submitted(self, event: Input.Submitted) -> None:
        value = event.value.strip()
        event.input.clear()
        if value:
            # Put into a queue; command loop processes sequentially.
            self._command_queue.put_nowait(value)
            # Echo the command to show it was received
            self.post_message(StatusMessage(f"[{datetime.now().strftime('%H:%M:%S')}] 👤 {value}"))

    async def _command_loop(self) -> None:
        while True:
            cmd = await self._command_queue.get()
            if self._engine is None:
                self.post_message(StatusMessage(f"[{datetime.now().strftime('%H:%M:%S')}] ⚠️ Engine not ready"))
                continue
            # Never run slow command parsing in the input handler; keep it in a worker task.
            try:
                await self._engine.handle_command(cmd)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self.post_message(
                    StatusMessage(
                        f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Command handler error: {type(exc).__name__}: {str(exc)[:200]}"
                    )
                )
                continue

            if not self._engine._running:
                self.post_message(QuitRequest())

    async def _run_engine(self) -> None:
        if not self.secrets.llm_api_key:
            self.post_message(StatusMessage("❌ Missing LLM API key"))
            return

        # Create primary UI (Textual)
        tui = _TextualUIAdapter(self)

        # Check if Telegram is enabled and create MultiUI
        if self.config.telegram.enabled and self.secrets.telegram_token:
            self.post_message(StatusMessage("🔧 Telegram enabled, initializing..."))
            try:
                telegram_ui = TelegramUI(
                    bot_token=self.secrets.telegram_token,
                    chat_id=self.config.telegram.chat_id,
                    on_chat_id=None,
                )
                ui = MultiUI(primary=tui, secondary=telegram_ui)
                self.post_message(StatusMessage("✅ Telegram UI initialized"))
            except Exception as exc:
                self.post_message(StatusMessage(f"⚠️  Telegram init failed: {type(exc).__name__}: {exc}"))
                ui = tui
        else:
            ui = tui

        self._client = MoltbookClient(self.config.moltbook.credentials_path)
        scheduler = Scheduler(self.config.behavior, self.config.advanced)
        llm = build_provider(self.config.llm, self.secrets.llm_api_key)
        self._engine = BotEngine(self.config, self._client, llm, scheduler, ui)
        try:
            # IMPORTANT: Start UI (launches Telegram polling if enabled)
            await ui.start()
            await self._engine.run_loop()
        finally:
            await ui.stop()
            await self._client.close()

    def set_agent_info(
        self,
        agent_name: str,
        profile_url: str | None,
        owner_name: str = "",
    ) -> None:
        label = Text()
        label.append("Agent: ", style="bold cyan")
        label.append(f"🦀 {agent_name}")

        if profile_url:
            label.append("\n")
            label.append(profile_url, style=f"link {profile_url} underline")

        if owner_name:
            label.append("\n")
            label.append("Owner: ", style="bold yellow")
            label.append(f"👤 {owner_name}")

        self.query_one("#header", Static).update(label)

    @on(QuitRequest)
    def _on_quit_request(self, _: QuitRequest) -> None:
        self.exit()
