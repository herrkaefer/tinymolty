#!/usr/bin/env python3
"""
Test API authentication for comment and upvote
"""
import asyncio
import json
from pathlib import Path

import httpx


async def test_api_calls():
    """Test comment and upvote API calls"""
    print("=" * 60)
    print("Testing Moltbook API Authentication")
    print("=" * 60)
    print()

    # Load credentials
    cred_path = Path("~/.config/moltbook/credentials.json").expanduser()
    with open(cred_path) as f:
        creds = json.load(f)

    api_key = creds.get("api_key")
    print(f"API Key: {api_key[:15]}...{api_key[-4:]}")
    print()

    base_url = "https://www.moltbook.com/api/v1"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        # First, get a post ID from feed
        print("-" * 60)
        print("1. Getting feed to find a post...")
        print("-" * 60)

        try:
            response = await client.get(f"{base_url}/feed", headers=headers)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                posts = data.get("posts", [])
                if posts:
                    post_id = posts[0].get("id")
                    post_content = posts[0].get("content", "")[:50]
                    print(f"✓ Got post ID: {post_id}")
                    print(f"  Content: {post_content}...")
                else:
                    print("✗ No posts in feed")
                    return
            else:
                print(f"✗ Failed: {response.text}")
                return
        except Exception as e:
            print(f"✗ Error: {e}")
            return

        print()

        # Test create post
        print("-" * 60)
        print("1.5 Testing create post...")
        print("-" * 60)
        print(f"URL: {base_url}/posts")

        try:
            response = await client.post(
                f"{base_url}/posts",
                headers=headers,
                json={
                    "submolt": "general",
                    "title": "Upvote/comment auth failing",
                    "content": "I can GET /agents/status and /agents/me, but POST upvote and comments return 401 Authentication required. Anyone else seeing this?"
                }
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")

            if response.status_code in (200, 201):
                print("✓ Create post successful!")
            else:
                print("✗ Create post failed")
        except Exception as e:
            print(f"✗ Error: {type(e).__name__}: {e}")
            if hasattr(e, 'response'):
                print(f"  Response: {e.response.text[:200]}")

        print()

        # Test upvote
        print("-" * 60)
        print("2. Testing upvote...")
        print("-" * 60)
        print(f"URL: {base_url}/posts/{post_id}/upvote")
        print(f"Headers: {headers}")

        try:
            response = await client.post(
                f"{base_url}/posts/{post_id}/upvote",
                headers=headers
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")

            if response.status_code == 200:
                print("✓ Upvote successful!")
            else:
                print(f"✗ Upvote failed")
        except Exception as e:
            print(f"✗ Error: {type(e).__name__}: {e}")
            if hasattr(e, 'response'):
                print(f"  Response: {e.response.text[:200]}")

        print()

        # Test comment
        print("-" * 60)
        print("3. Testing comment...")
        print("-" * 60)
        print(f"URL: {base_url}/posts/{post_id}/comments")

        try:
            response = await client.post(
                f"{base_url}/posts/{post_id}/comments",
                headers=headers,
                json={"content": "Test comment from TinyMolty"}
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:200]}")

            if response.status_code in (200, 201):
                print("✓ Comment successful!")
            else:
                print(f"✗ Comment failed")
        except Exception as e:
            print(f"✗ Error: {type(e).__name__}: {e}")
            if hasattr(e, 'response'):
                print(f"  Response: {e.response.text[:200]}")

    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_api_calls())
