import asyncio
import json
from pathlib import Path
import httpx

async def check_feed():
    cred_path = Path("~/.config/moltbook/credentials.json").expanduser()
    with open(cred_path) as f:
        creds = json.load(f)
    
    api_key = creds.get("api_key")
    headers = {"Authorization": f"Bearer {api_key}"}
    
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            "https://www.moltbook.com/api/v1/feed",
            headers=headers
        )
        data = resp.json()
        
        # Show first post in detail
        if data.get("posts"):
            post = data["posts"][0]
            print("First post (raw):")
            print(json.dumps(post, indent=2, default=str))
            
            # Try upvoting
            post_id = post["id"]
            print(f"\n\nTrying to upvote {post_id}...")
            
            try:
                upvote_resp = await client.post(
                    f"https://www.moltbook.com/api/v1/posts/{post_id}/upvote",
                    headers=headers
                )
                print(f"Status: {upvote_resp.status_code}")
                print(f"Response: {upvote_resp.text}")
            except httpx.HTTPStatusError as e:
                print(f"Status: {e.response.status_code}")
                print(f"Response: {e.response.text}")
                print(f"\nRequest headers: {e.request.headers}")

asyncio.run(check_feed())
