import asyncio
import json
from pathlib import Path
import httpx

async def test_all():
    cred_path = Path("~/.config/moltbook/credentials.json").expanduser()
    with open(cred_path) as f:
        api_key = json.load(f)["api_key"]
    
    headers = {"Authorization": f"Bearer {api_key}"}
    base = "https://www.moltbook.com/api/v1"
    
    async with httpx.AsyncClient() as client:
        tests = [
            ("Comment", "POST", f"{base}/posts/b52190c2-4638-483f-a338-67f4cd75f086/comments", {"content": "test"}),
            ("Upvote", "POST", f"{base}/posts/b52190c2-4638-483f-a338-67f4cd75f086/upvote", None),
            ("Subscribe", "POST", f"{base}/submolts/general/subscribe", None),
            ("Follow", "POST", f"{base}/agents/rapidpixel/follow", None),
        ]
        
        for name, method, url, json_data in tests:
            try:
                resp = await client.request(method, url, headers=headers, json=json_data)
                print(f"✓ {name}: {resp.status_code} - {resp.text[:60]}")
            except httpx.HTTPStatusError as e:
                print(f"✗ {name}: {e.response.status_code} - {e.response.text[:60]}")

asyncio.run(test_all())
