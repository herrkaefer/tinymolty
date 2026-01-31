from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import httpx

from .models import CreatePostResponse, FeedResponse, Post
from .rate_limiter import RateLimiter


class MoltbookClient:
    def __init__(
        self,
        credentials_path: str,
        base_url: str = "https://www.moltbook.com/api/v1",
        rate_limiter: RateLimiter | None = None,
    ) -> None:
        self.credentials_path = Path(credentials_path).expanduser()
        self.base_url = base_url.rstrip("/")
        self.rate_limiter = rate_limiter or RateLimiter()
        self._token = self._load_token()
        self._client = httpx.AsyncClient(timeout=30.0)

    def _load_token(self) -> str | None:
        if not self.credentials_path.exists():
            return None
        data = json.loads(self.credentials_path.read_text())
        return data.get("api_key") or data.get("token")

    def _auth_headers(self) -> dict[str, str]:
        if not self._token:
            return {}
        return {"Authorization": f"Bearer {self._token}"}

    async def close(self) -> None:
        await self._client.aclose()

    async def _request(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        await self.rate_limiter.wait()
        url = f"{self.base_url}{path}"
        headers = kwargs.pop("headers", {})
        headers.update(self._auth_headers())
        response = await self._client.request(method, url, headers=headers, **kwargs)
        response.raise_for_status()
        return response

    async def get_feed(self) -> FeedResponse:
        response = await self._request("GET", "/feed")
        payload = response.json()
        posts = [Post.model_validate(item | {"raw": item}) for item in payload.get("posts", [])]
        return FeedResponse(posts=posts)

    async def upvote(self, post_id: str) -> None:
        await self._request("POST", f"/posts/{post_id}/upvote")

    async def comment(self, post_id: str, content: str) -> None:
        await self._request("POST", f"/posts/{post_id}/comment", json={"content": content})

    async def follow(self, agent_id: str) -> None:
        await self._request("POST", f"/agents/{agent_id}/follow")

    async def create_post(self, content: str, submolt: str | None = None) -> CreatePostResponse:
        payload: dict[str, Any] = {"content": content}
        if submolt:
            payload["submolt"] = submolt
        response = await self._request("POST", "/posts", json=payload)
        return CreatePostResponse.model_validate(response.json())

    async def heartbeat(self) -> None:
        await self._request("POST", "/agents/heartbeat")

    async def get_me(self) -> dict[str, Any]:
        response = await self._request("GET", "/agents/me")
        return response.json()
