#!/usr/bin/env python3
"""
Moltbook Account Setup Helper
Assists users in registering Moltbook accounts and configuring credentials
"""
import json
import sys
from pathlib import Path
from getpass import getpass


def print_banner():
    print("=" * 60)
    print("🦀 Moltbook Account Setup Helper")
    print("=" * 60)
    print()


def check_credentials_exist():
    """Check if credentials file already exists"""
    cred_path = Path("~/.config/moltbook/credentials.json").expanduser()
    if cred_path.exists():
        print(f"✓ Found existing credentials: {cred_path}")
        try:
            data = json.loads(cred_path.read_text())
            token = data.get("api_key") or data.get("token")
            if token:
                print(f"✓ Credentials configured (Token: {token[:10]}...)")
                return True
        except Exception:
            pass
    return False


def guide_manual_registration():
    """Guide user through manual registration"""
    print("\n📋 Moltbook Account Registration Steps:")
    print()
    print("1. Open browser and visit: https://moltbook.com")
    print("2. Click 'Sign Up' or 'Register' button")
    print("3. Fill in registration information:")
    print("   - Username")
    print("   - Email address")
    print("   - Password")
    print("4. Complete registration and verify email (if required)")
    print("5. Log in to your account")
    print("6. Navigate to account settings")
    print("7. Find 'API Token' or 'API Key' section")
    print("8. Copy your API Token")
    print()

    input("After completing these steps, press Enter to continue...")


def create_credentials_file():
    """Create credentials file"""
    print("\n🔑 Configure API Token")
    print()

    # Get API Token
    token = getpass("Please paste your Moltbook API Token (hidden): ").strip()

    if not token:
        print("✗ No token provided, exiting")
        sys.exit(1)

    # Confirm Token
    print(f"\nToken preview: {token[:10]}...{token[-4:] if len(token) > 14 else ''}")
    confirm = input("Confirm this is the correct token? (y/n): ").lower()

    if confirm != 'y':
        print("✗ Cancelled")
        sys.exit(1)

    # Create directory
    cred_dir = Path("~/.config/moltbook").expanduser()
    cred_dir.mkdir(parents=True, exist_ok=True)

    # Create credentials file
    cred_path = cred_dir / "credentials.json"
    credentials = {
        "api_key": token
    }

    cred_path.write_text(json.dumps(credentials, indent=2))
    cred_path.chmod(0o600)

    print(f"\n✓ Credentials file created: {cred_path}")
    print(f"✓ File permissions set to 600 (owner read/write only)")

    return cred_path


def verify_credentials():
    """Verify credentials file"""
    print("\n🔍 Verifying credentials configuration...")

    cred_path = Path("~/.config/moltbook/credentials.json").expanduser()

    if not cred_path.exists():
        print("✗ Credentials file not found")
        return False

    try:
        data = json.loads(cred_path.read_text())
        token = data.get("api_key") or data.get("token")

        if not token:
            print("✗ Token not found in credentials file")
            return False

        print(f"✓ Token configured: {token[:10]}...")

        # Check file permissions
        import stat
        mode = cred_path.stat().st_mode
        mode_str = stat.filemode(mode)
        print(f"✓ File permissions: {mode_str}")

        if mode & 0o077:
            print("⚠ Warning: File permissions too permissive, recommend 600")
            if input("Fix permissions? (y/n): ").lower() == 'y':
                cred_path.chmod(0o600)
                print("✓ Permissions fixed")

        return True

    except json.JSONDecodeError:
        print("✗ Invalid credentials file format (not valid JSON)")
        return False
    except Exception as e:
        print(f"✗ Verification failed: {e}")
        return False


def test_connection():
    """Test API connection"""
    print("\n🌐 Testing Moltbook API connection...")

    try:
        import asyncio
        import httpx

        async def check_api():
            cred_path = Path("~/.config/moltbook/credentials.json").expanduser()
            data = json.loads(cred_path.read_text())
            token = data.get("api_key") or data.get("token")

            headers = {"Authorization": f"Bearer {token}"}

            async with httpx.AsyncClient(timeout=10.0) as client:
                try:
                    response = await client.get(
                        "https://www.moltbook.com/api/v1/agents/me",
                        headers=headers
                    )

                    if response.status_code == 200:
                        user_data = response.json()
                        print(f"✓ API connection successful!")
                        print(f"✓ Account info:")
                        print(f"  - ID: {user_data.get('id', 'N/A')}")
                        print(f"  - Name: {user_data.get('name', 'N/A')}")
                        return True
                    else:
                        print(f"✗ API returned error: {response.status_code}")
                        print(f"  Response: {response.text[:200]}")
                        return False

                except httpx.HTTPError as e:
                    print(f"✗ API connection failed: {e}")
                    return False

        result = asyncio.run(check_api())
        return result

    except ImportError:
        print("⚠ httpx not installed, skipping API test")
        print("  Run this script in virtual environment to enable testing")
        return None
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


def show_next_steps():
    """Show next steps"""
    print("\n" + "=" * 60)
    print("🎉 Moltbook Account Configuration Complete!")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Run TinyMolty setup wizard:")
    print("   python -m tinymolty --setup")
    print()
    print("2. Or start TinyMolty directly:")
    print("   python -m tinymolty")
    print()


def main():
    """Main function"""
    print_banner()

    # Check for existing credentials
    if check_credentials_exist():
        print()
        choice = input("Credentials already exist. Reconfigure? (y/n): ").lower()
        if choice != 'y':
            print("\nKeeping existing configuration.")

            # Optional: verify and test
            if input("\nVerify existing credentials? (y/n): ").lower() == 'y':
                if verify_credentials():
                    test_connection()

            show_next_steps()
            return

    # Guide registration
    print("\nDon't have a Moltbook account yet?")
    print("1. I already have an account and API Token")
    print("2. I need to register a new account")
    print("3. Exit")

    choice = input("\nPlease select (1-3): ").strip()

    if choice == '1':
        # Configure credentials directly
        cred_path = create_credentials_file()
        if verify_credentials():
            test_connection()
        show_next_steps()

    elif choice == '2':
        # Guide registration
        guide_manual_registration()
        cred_path = create_credentials_file()
        if verify_credentials():
            test_connection()
        show_next_steps()

    elif choice == '3':
        print("\nExiting.")
        sys.exit(0)

    else:
        print("\n✗ Invalid selection")
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Cancelled")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
