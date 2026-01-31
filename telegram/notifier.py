from __future__ import annotations

import httpx


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot_token = bot_token
        self.chat_id = chat_id
        self._client = httpx.AsyncClient(timeout=20.0)

    async def close(self) -> None:
        await self._client.aclose()

    async def send(self, text: str) -> None:
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text}
        response = await self._client.post(url, json=payload)
        response.raise_for_status()
