import asyncio
import json
import os
from pathlib import Path

import httpx
import pytest


def test_create_post_integration() -> None:
    if os.getenv("TINYMOLTY_INTEGRATION_TESTS") != "1":
        pytest.skip("Integration test (set TINYMOLTY_INTEGRATION_TESTS=1 to run)")

    cred_path = Path("~/.config/moltbook/credentials.json").expanduser()
    if not cred_path.exists():
        pytest.skip(f"Missing credentials at {cred_path}")

    async def _run() -> None:
        with open(cred_path) as f:
            api_key = json.load(f)["api_key"]

        headers = {"Authorization": f"Bearer {api_key}"}

        async with httpx.AsyncClient() as client:
            me_resp = await client.get(
                "https://www.moltbook.com/api/v1/agents/me",
                headers=headers,
            )
            assert me_resp.status_code < 500, me_resp.text[:200]

            payload = {
                "submolt": "introductions",
                "title": "Hello from TinyMolty",
                "content": "Just testing the API. Please ignore this test post!",
            }
            resp = await client.post(
                "https://www.moltbook.com/api/v1/posts",
                headers=headers,
                json=payload,
            )
            assert resp.status_code < 500, resp.text[:200]

    asyncio.run(_run())
