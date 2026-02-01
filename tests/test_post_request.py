#!/usr/bin/env python3
"""
Test creating a post to verify POST authentication works
"""
import asyncio
import json
from pathlib import Path

import httpx


async def test_create_post():
    """Test if POST request works for creating a post"""
    print("=" * 60)
    print("Testing POST /posts (create post)")
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

    async with httpx.AsyncClient(timeout=30.0) as client:
        # Test 1: Without Content-Type
        print("-" * 60)
        print("Test 1: POST /posts WITHOUT Content-Type header")
        print("-" * 60)

        headers1 = {
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "submolt": "general",
            "title": "Test post from TinyMolty",
            "content": "Testing authentication for POST requests"
        }

        try:
            response = await client.post(
                f"{base_url}/posts",
                headers=headers1,
                json=payload
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:300]}")
        except Exception as e:
            print(f"Error: {e}")
            if hasattr(e, 'response'):
                print(f"Status: {e.response.status_code}")
                print(f"Response: {e.response.text[:300]}")

        print()

        # Test 2: With Content-Type
        print("-" * 60)
        print("Test 2: POST /posts WITH Content-Type header")
        print("-" * 60)

        headers2 = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        try:
            response = await client.post(
                f"{base_url}/posts",
                headers=headers2,
                json=payload
            )
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text[:300]}")
        except Exception as e:
            print(f"Error: {e}")
            if hasattr(e, 'response'):
                print(f"Status: {e.response.status_code}")
                print(f"Response: {e.response.text[:300]}")

        print()

        # Test 3: Check headers that httpx actually sends
        print("-" * 60)
        print("Test 3: Inspect actual headers sent by httpx")
        print("-" * 60)

        # Create request without sending
        request = client.build_request(
            "POST",
            f"{base_url}/posts",
            headers=headers2,
            json=payload
        )
        print("Headers that will be sent:")
        for key, value in request.headers.items():
            if key.lower() == 'authorization':
                print(f"  {key}: {value[:30]}...")
            else:
                print(f"  {key}: {value}")

    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_create_post())
