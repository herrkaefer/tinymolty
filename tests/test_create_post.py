import asyncio
import json
from pathlib import Path
import httpx

async def test():
    cred_path = Path("~/.config/moltbook/credentials.json").expanduser()
    with open(cred_path) as f:
        api_key = json.load(f)["api_key"]
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    async with httpx.AsyncClient() as client:
        # Get my subscriptions first
        me_resp = await client.get(
            "https://www.moltbook.com/api/v1/agents/me",
            headers=headers
        )
        subs = me_resp.json()["agent"]["stats"]["subscriptions"]
        print(f"I have {subs} subscriptions")
        
        # Try creating a post in general
        payload = {
            "submolt": "introductions",
            "title": "Hello from TinyMolty",
            "content": "Just testing the API. Please ignore this test post!"
        }
        
        try:
            resp = await client.post(
                "https://www.moltbook.com/api/v1/posts",
                headers=headers,
                json=payload
            )
            print(f"\nCreate post: {resp.status_code}")
            print(f"Response: {resp.text}")
        except httpx.HTTPStatusError as e:
            print(f"\nCreate post: {e.response.status_code}")
            print(f"Response: {e.response.text}")

asyncio.run(test())
