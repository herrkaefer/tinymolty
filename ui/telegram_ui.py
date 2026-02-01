from __future__ import annotations

import asyncio

import httpx

from .base import UserInterface


class TelegramUI(UserInterface):
    def __init__(
        self,
        bot_token: str,
        chat_id: str | None,
        on_chat_id: callable | None = None,
    ) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id or ""
        self._on_chat_id = on_chat_id
        self._client = httpx.AsyncClient(timeout=30.0)
        self._poll_task: asyncio.Task | None = None
        self._command_queue: asyncio.Queue[str] = asyncio.Queue()
        self._reply_queue: asyncio.Queue[str] = asyncio.Queue()
        self._running = False
        self._offset = 0

    async def start(self) -> None:
        self._running = True
        await self._set_bot_commands()
        self._poll_task = asyncio.create_task(self._poll())

    async def stop(self) -> None:
        self._running = False
        if self._poll_task:
            self._poll_task.cancel()
        await self._client.aclose()

    async def send_status(self, message: str) -> None:
        await self._send_message(message)

    async def prompt(self, message: str) -> str:
        await self._send_message(message)
        return await self._reply_queue.get()

    async def get_command(self) -> str | None:
        if self._command_queue.empty():
            return None
        return self._command_queue.get_nowait()

    async def update_activity(self, message: str, next_action_seconds: float | None = None) -> None:
        # In Telegram mode, only send key activities, skip routine status updates
        # Skip messages like "Sleeping" to avoid spam
        if message.lower().startswith("sleeping"):
            return
        # Send key activities only
        await self.send_status(message)

    async def _send_message(self, text: str) -> None:
        if not self.chat_id:
            return
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text}
        response = await self._client.post(url, json=payload)
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            detail = response.text[:200]
            raise httpx.HTTPStatusError(
                f"{exc} - response: {detail}", request=exc.request, response=exc.response
            ) from None

    async def _set_bot_commands(self) -> None:
        url = f"https://api.telegram.org/bot{self.bot_token}/setMyCommands"
        payload = {
            "commands": [
                {"command": "status", "description": "Show current status"},
                {"command": "pause", "description": "Pause the agent"},
                {"command": "resume", "description": "Resume the agent"},
                {"command": "quit", "description": "Shut down gracefully"},
            ]
        }
        try:
            response = await self._client.post(url, json=payload)
            response.raise_for_status()
        except Exception:
            # Ignore failures; bot can still operate without the menu.
            return

    async def _poll(self) -> None:
        url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
        while self._running:
            response = await self._client.get(
                url, params={"timeout": 5, "offset": self._offset}
            )
            response.raise_for_status()
            data = response.json()
            for update in data.get("result", []):
                self._offset = max(self._offset, update.get("update_id", 0) + 1)
                message = update.get("message") or {}
                chat = message.get("chat") or {}
                if not self.chat_id:
                    new_chat_id = str(chat.get("id") or "")
                    if new_chat_id:
                        self.chat_id = new_chat_id
                        if self._on_chat_id:
                            await self._on_chat_id(self.chat_id)
                        await self._send_message("✅ Telegram chat linked. Commands are now active.")
                if self.chat_id and str(chat.get("id")) != str(self.chat_id):
                    continue
                text = (message.get("text") or "").strip()
                if not text:
                    continue
                if text.startswith("/"):
                    command = text.lstrip("/").split()[0].lower()
                    if command in {"pause", "resume", "status", "quit"}:
                        await self._command_queue.put(command)
                    else:
                        await self._command_queue.put(command)
                else:
                    await self._reply_queue.put(text)
            await asyncio.sleep(0.1)
