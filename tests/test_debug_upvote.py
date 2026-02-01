#!/usr/bin/env python3
"""
Debug upvote 401 error in detail
"""
import asyncio
import json
from pathlib import Path

import httpx


async def debug_upvote():
    """Debug upvote authentication"""
    print("=" * 60)
    print("Debugging Upvote 401 Error")
    print("=" * 60)
    print()

    # Load credentials
    cred_path = Path("~/.config/moltbook/credentials.json").expanduser()
    with open(cred_path) as f:
        creds = json.load(f)

    api_key = creds.get("api_key")
    base_url = "https://www.moltbook.com/api/v1"

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get multiple posts
        print("-" * 60)
        print("Getting multiple posts from feed...")
        print("-" * 60)

        headers = {"Authorization": f"Bearer {api_key}"}
        feed_response = await client.get(f"{base_url}/feed", headers=headers)

        posts = feed_response.json().get("posts", [])
        print(f"Got {len(posts)} posts\n")

        # Try upvoting multiple different posts
        for i, post in enumerate(posts[:3]):
            post_id = post["id"]
            author = post.get("author", {})
            author_name = author.get("name") if isinstance(author, dict) else "Unknown"

            print(f"Post {i+1}: {post_id}")
            print(f"  Author: {author_name}")
            print(f"  Content: {post.get('content', '')[:50]}...")

            # Try upvote with different header combinations
            print(f"  Testing upvote...")

            # Test 1: Minimal headers
            try:
                resp = await client.post(
                    f"{base_url}/posts/{post_id}/upvote",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                print(f"    Status: {resp.status_code}")
                if resp.status_code != 200:
                    print(f"    Response: {resp.text}")
                else:
                    print(f"    ✓ Success!")
            except httpx.HTTPStatusError as e:
                print(f"    Status: {e.response.status_code}")
                print(f"    Response: {e.response.text}")
            except Exception as e:
                print(f"    Error: {e}")

            print()

        # Try heartbeat (should work)
        print("-" * 60)
        print("Testing heartbeat (should work)...")
        print("-" * 60)

        try:
            resp = await client.post(
                f"{base_url}/agents/heartbeat",
                headers={"Authorization": f"Bearer {api_key}"}
            )
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
        except Exception as e:
            print(f"Error: {e}")
            if hasattr(e, 'response'):
                print(f"Response: {e.response.text}")

        print()

        # Compare request details
        print("-" * 60)
        print("Comparing request details:")
        print("-" * 60)

        # Build requests without sending
        heartbeat_req = client.build_request(
            "POST",
            f"{base_url}/agents/heartbeat",
            headers={"Authorization": f"Bearer {api_key}"}
        )

        upvote_req = client.build_request(
            "POST",
            f"{base_url}/posts/{posts[0]['id']}/upvote",
            headers={"Authorization": f"Bearer {api_key}"}
        )

        print("\nHeartbeat request:")
        print(f"  URL: {heartbeat_req.url}")
        print(f"  Method: {heartbeat_req.method}")
        print(f"  Headers:")
        for k, v in heartbeat_req.headers.items():
            if 'auth' in k.lower():
                print(f"    {k}: {v[:30]}...")
            else:
                print(f"    {k}: {v}")

        print("\nUpvote request:")
        print(f"  URL: {upvote_req.url}")
        print(f"  Method: {upvote_req.method}")
        print(f"  Headers:")
        for k, v in upvote_req.headers.items():
            if 'auth' in k.lower():
                print(f"    {k}: {v[:30]}...")
            else:
                print(f"    {k}: {v}")

    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(debug_upvote())
