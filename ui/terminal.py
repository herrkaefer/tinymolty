from __future__ import annotations

import asyncio
from collections import deque
from typing import Deque

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.text import Text

from .base import UserInterface


class TerminalUI(UserInterface):
    def __init__(self) -> None:
        self.console = Console()
        self._command_queue: asyncio.Queue[str] = asyncio.Queue()
        self._logs: Deque[str] = deque(maxlen=200)
        self._activity: str = "Idle"
        self._next_action_seconds: float | None = None
        self._live_task: asyncio.Task | None = None
        self._input_task: asyncio.Task | None = None
        self._running = False

    async def start(self) -> None:
        self._running = True
        self._live_task = asyncio.create_task(self._run_live())
        self._input_task = asyncio.create_task(self._read_input())

    async def stop(self) -> None:
        self._running = False
        for task in (self._live_task, self._input_task):
            if task:
                task.cancel()
        await asyncio.sleep(0)

    async def send_status(self, message: str) -> None:
        self._logs.append(message)

    async def prompt(self, message: str) -> str:
        self.console.print(message)
        return await asyncio.to_thread(input, "> ")

    async def get_command(self) -> str | None:
        if self._command_queue.empty():
            return None
        return self._command_queue.get_nowait()

    async def update_activity(self, message: str, next_action_seconds: float | None = None) -> None:
        self._activity = message
        self._next_action_seconds = next_action_seconds

    async def _read_input(self) -> None:
        while self._running:
            raw = await asyncio.to_thread(input, "")
            if not raw:
                continue
            cmd = raw.strip().lower()
            if cmd in {"p", "pause"}:
                await self._command_queue.put("pause")
            elif cmd in {"r", "resume"}:
                await self._command_queue.put("resume")
            elif cmd in {"q", "quit", "exit"}:
                await self._command_queue.put("quit")
            elif cmd in {"s", "status"}:
                await self._command_queue.put("status")
            else:
                await self._command_queue.put(cmd)

    def _render_panel(self) -> Panel:
        header = Text(f"Activity: {self._activity}")
        if self._next_action_seconds is not None:
            header.append(f" | Next action in ~{int(self._next_action_seconds)}s")
        body = "\n".join(list(self._logs)[-15:]) or "No activity yet."
        return Panel(body, title=header, border_style="green")

    async def _run_live(self) -> None:
        with Live(self._render_panel(), console=self.console, refresh_per_second=2) as live:
            while self._running:
                live.update(self._render_panel())
                await asyncio.sleep(0.5)
