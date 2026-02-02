import asyncio
import json
import os
from pathlib import Path

import httpx
import pytest


def test_all_posts_integration() -> None:
    if os.getenv("TINYMOLTY_INTEGRATION_TESTS") != "1":
        pytest.skip("Integration test (set TINYMOLTY_INTEGRATION_TESTS=1 to run)")

    cred_path = Path("~/.config/moltbook/credentials.json").expanduser()
    if not cred_path.exists():
        pytest.skip(f"Missing credentials at {cred_path}")

    async def _run() -> None:
        with open(cred_path) as f:
            api_key = json.load(f)["api_key"]

        headers = {"Authorization": f"Bearer {api_key}"}
        base = "https://www.moltbook.com/api/v1"

        async with httpx.AsyncClient() as client:
            tests = [
                (
                    "Comment",
                    "POST",
                    f"{base}/posts/b52190c2-4638-483f-a338-67f4cd75f086/comments",
                    {"content": "test"},
                ),
                ("Upvote", "POST", f"{base}/posts/b52190c2-4638-483f-a338-67f4cd75f086/upvote", None),
                ("Subscribe", "POST", f"{base}/submolts/general/subscribe", None),
                ("Follow", "POST", f"{base}/agents/rapidpixel/follow", None),
            ]

            for name, method, url, json_data in tests:
                resp = await client.request(method, url, headers=headers, json=json_data)
                assert resp.status_code < 500, f"{name} failed: {resp.status_code} {resp.text[:120]}"

    asyncio.run(_run())
