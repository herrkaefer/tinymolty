#!/usr/bin/env python3
"""
Get available submolts and test posting
"""
import asyncio
import json
from pathlib import Path

import httpx


async def test_submolts_and_post():
    """Get submolts and try posting to a real one"""
    print("=" * 60)
    print("Testing Submolts and Posting")
    print("=" * 60)
    print()

    # Load credentials
    cred_path = Path("~/.config/moltbook/credentials.json").expanduser()
    with open(cred_path) as f:
        creds = json.load(f)

    api_key = creds.get("api_key")
    base_url = "https://www.moltbook.com/api/v1"
    headers = {"Authorization": f"Bearer {api_key}"}

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Get available submolts
        print("-" * 60)
        print("1. Getting available submolts...")
        print("-" * 60)

        try:
            response = await client.get(f"{base_url}/submolts", headers=headers)
            print(f"Status: {response.status_code}")

            if response.status_code == 200:
                data = response.json()
                submolts = data.get("submolts", []) if isinstance(data, dict) else data
                print(f"Found {len(submolts)} submolts:")
                for s in submolts[:10]:
                    name = s.get("name") if isinstance(s, dict) else s
                    print(f"  - {name}")

                # Use first submolt for testing
                if submolts:
                    test_submolt = submolts[0].get("name") if isinstance(submolts[0], dict) else submolts[0]
                    print(f"\nWill use '{test_submolt}' for testing")
                else:
                    test_submolt = None
                    print("\n⚠️  No submolts found, will try without submolt")
            else:
                print(f"Failed: {response.text}")
                test_submolt = None
        except Exception as e:
            print(f"Error: {e}")
            test_submolt = None

        print()

        # Try posting
        print("-" * 60)
        print("2. Testing POST /posts...")
        print("-" * 60)

        payload = {
            "title": "Test from TinyMolty API",
            "content": "Testing authentication and posting functionality"
        }

        if test_submolt:
            payload["submolt"] = test_submolt

        print(f"Payload: {payload}")
        print()

        try:
            response = await client.post(
                f"{base_url}/posts",
                headers=headers,
                json=payload
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:500]}")
        except Exception as e:
            print(f"Error: {e}")
            if hasattr(e, 'response'):
                print(f"Status: {e.response.status_code}")
                print(f"Response: {e.response.text[:500]}")

        print()

        # Now test upvote on an existing post
        print("-" * 60)
        print("3. Testing upvote on existing post...")
        print("-" * 60)

        # Get a post from feed first
        feed_response = await client.get(f"{base_url}/feed", headers=headers)
        if feed_response.status_code == 200:
            posts = feed_response.json().get("posts", [])
            if posts:
                post_id = posts[0]["id"]
                print(f"Post ID: {post_id}")

                try:
                    response = await client.post(
                        f"{base_url}/posts/{post_id}/upvote",
                        headers=headers
                    )
                    print(f"Status: {response.status_code}")
                    print(f"Response: {response.text[:300]}")
                except Exception as e:
                    print(f"Error: {e}")
                    if hasattr(e, 'response'):
                        print(f"Status: {e.response.status_code}")
                        print(f"Response: {e.response.text[:300]}")

    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_submolts_and_post())
