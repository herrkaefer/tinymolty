import asyncio
import json
from pathlib import Path
import httpx

async def check_status():
    cred_path = Path("~/.config/moltbook/credentials.json").expanduser()
    with open(cred_path) as f:
        creds = json.load(f)
    
    api_key = creds.get("api_key")
    headers = {"Authorization": f"Bearer {api_key}"}
    
    async with httpx.AsyncClient() as client:
        # Check status
        resp = await client.get(
            "https://www.moltbook.com/api/v1/agents/status",
            headers=headers
        )
        print(f"Status check: {resp.status_code}")
        print(f"Response: {resp.text}")
        
        # Check me
        resp2 = await client.get(
            "https://www.moltbook.com/api/v1/agents/me",
            headers=headers
        )
        print(f"\nMe: {resp2.status_code}")
        data = resp2.json()
        agent = data.get("agent", {})
        print(f"Name: {agent.get('name')}")
        print(f"Claimed: {agent.get('is_claimed')}")
        print(f"Karma: {agent.get('karma')}")
        print(f"Posts: {agent.get('stats', {}).get('posts')}")
        print(f"Comments: {agent.get('stats', {}).get('comments')}")

asyncio.run(check_status())
