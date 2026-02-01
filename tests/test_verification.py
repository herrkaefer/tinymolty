#!/usr/bin/env python3
"""
Test script to verify Moltbook account status
"""
import asyncio
import json
from pathlib import Path

from moltbook.client import MoltbookClient


async def test_verification():
    """Test account verification"""
    print("=" * 60)
    print("Testing Moltbook Account Verification")
    print("=" * 60)
    print()

    # Load credentials
    cred_path = Path("~/.config/moltbook/credentials.json").expanduser()
    if not cred_path.exists():
        print(f"❌ Credentials not found at: {cred_path}")
        return

    print(f"✓ Found credentials at: {cred_path}")

    # Show credentials content (masked)
    with open(cred_path) as f:
        creds = json.load(f)

    print()
    print("Credentials content:")
    for key, value in creds.items():
        if key in ("api_key", "token"):
            masked = f"{value[:10]}...{value[-4:]}" if len(value) > 14 else "***"
            print(f"  {key}: {masked}")
        else:
            print(f"  {key}: {value}")

    print()
    print("-" * 60)
    print("Testing API call: GET /agents/me")
    print("-" * 60)

    client = MoltbookClient(str(cred_path))

    try:
        me = await client.get_me()
        print()
        print("✅ API call successful!")
        print()
        print("Response data:")
        print(json.dumps(me, indent=2, default=str))
        print()

        # Try to extract common fields
        print("-" * 60)
        print("Field analysis:")
        print("-" * 60)

        possible_name_fields = ["name", "agent_name", "username", "display_name"]
        for field in possible_name_fields:
            if field in me:
                print(f"  ✓ {field}: {me[field]}")

        possible_verified_fields = ["verified", "is_verified", "claimed", "status"]
        for field in possible_verified_fields:
            if field in me:
                print(f"  ✓ {field}: {me[field]}")

    except Exception as e:
        print()
        print(f"❌ API call failed!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {str(e)}")
        print()

        # Show more details for HTTP errors
        if hasattr(e, 'response'):
            print(f"HTTP Status: {e.response.status_code}")
            print(f"Response body: {e.response.text[:500]}")

    finally:
        await client.close()

    print()
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_verification())
