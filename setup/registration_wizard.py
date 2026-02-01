"""
Moltbook registration wizard
Simple command-line interface for registering new agents
"""
from __future__ import annotations

import asyncio
from pathlib import Path


def print_header():
    """Print registration header"""
    print()
    print("=" * 60)
    print("🦀 Moltbook Agent Registration")
    print("=" * 60)
    print()
    print("Welcome to TinyMolty!")
    print()
    print("First-time setup requires registering a Moltbook agent account.")
    print("After registration, you'll receive an API key to access Moltbook.")
    print()


def get_agent_info() -> tuple[str, str] | None:
    """Get agent name and description from user"""
    print("Please provide your agent information:")
    print()

    # Get agent name
    while True:
        name = input("Agent Name (e.g., CuriousMolty, TechCrab): ").strip()
        if name:
            break
        print("❌ Agent name cannot be empty. Please try again.")
        print()

    # Get agent description
    while True:
        description = input("Agent Description (e.g., A curious AI agent): ").strip()
        if description:
            break
        print("❌ Description cannot be empty. Please try again.")
        print()

    # Confirm
    print()
    print("=" * 60)
    print(f"Agent Name: {name}")
    print(f"Description: {description}")
    print("=" * 60)
    print()

    while True:
        confirm = input("Proceed with registration? (y/n) [y]: ").lower().strip()

        # Default to 'y' if user just presses Enter
        if confirm == '' or confirm == 'y':
            return name, description
        elif confirm == 'n':
            print()
            print("❌ Registration cancelled (you chose 'n').")
            return None
        else:
            print()
            print(f"❌ Invalid input: '{confirm}'")
            print("   Please enter 'y' to proceed or 'n' to cancel.")
            print()


async def register_agent_cli(
    name: str,
    description: str,
    credentials_path: str | None = None,
) -> dict | None:
    """Register agent and return registration data"""
    from moltbook.registration import register_agent, save_credentials

    print()
    print(f"⏳ Registering {name}...")
    print()

    try:
        response = await register_agent(name, description)

        # Save credentials
        cred_path = save_credentials(
            response.api_key,
            response.agent_name,
            credentials_path=credentials_path or "~/.config/moltbook/credentials.json",
        )

        # Print success message
        print("=" * 60)
        print("✅ Registration Successful!")
        print("=" * 60)
        print()
        print("📋 Account Information:")
        print(f"  • Agent Name: {response.agent_name}")
        print(f"  • API Key: {response.api_key[:15]}...{response.api_key[-4:]}")
        print()
        print("🔗 Claim URL (IMPORTANT - save this!):")
        print(f"  {response.claim_url}")
        print()
        print("🔑 Verification Code:")
        print(f"  {response.verification_code}")
        print()
        print("💾 Credentials saved to:")
        print(f"  {cred_path}")
        print()
        print("⚠️  Next Steps:")
        print("  1. Visit the claim URL above to complete human verification")
        print("  2. You'll need the verification code during the claim process")
        print("  3. Your account can only be used after verification")
        print("  4. Keep your API key secure!")
        print()
        print("=" * 60)

        return {
            "api_key": response.api_key,
            "agent_name": response.agent_name,
            "claim_url": response.claim_url,
            "verification_code": response.verification_code,
            "credentials_path": str(cred_path)
        }

    except Exception as e:
        print("=" * 60)
        print(f"❌ Registration Failed")
        print("=" * 60)
        print()
        print(f"Error: {str(e)}")
        print()

        # Show error type for debugging
        error_type = type(e).__name__
        print(f"Error type: {error_type}")
        print()

        print("Possible reasons:")
        print("  • Network connection issue")
        print("  • Agent name already taken")
        print("  • API service temporarily unavailable")
        print("  • Invalid API response")
        print()
        print("Suggestions:")
        print("  1. Check your network connection")
        print("  2. Try a different agent name")
        print("  3. Check if you can access https://www.moltbook.com")
        print("  4. Retry later")
        print()

        # Optionally show full traceback in verbose mode
        import os
        if os.getenv("DEBUG"):
            import traceback
            print("Full error trace (DEBUG mode):")
            traceback.print_exc()
            print()

        return None


def run_registration_wizard(
    credentials_exist: bool = False,
    credentials_path: str | None = None,
) -> dict | None:
    """
    Run the registration wizard

    Args:
        credentials_exist: Whether credentials file already exists

    Returns:
        Registration data dict, or None if user skipped (only when credentials exist)
    """
    print_header()

    if credentials_exist:
        # User already has credentials, give them a choice
        print("Existing Moltbook credentials detected.")
        print()
        print("Choose an option:")
        print("  1. Use existing account (skip registration)")
        print("  2. Register a new account")
        print()

        while True:
            choice = input("Enter choice (1 or 2): ").strip()

            if choice == '1':
                print()
                print("✓ Using existing Moltbook credentials.")
                print()
                return None

            if choice == '2':
                print()
                print("⚠️  This will create a NEW account.")
                print("   Your existing credentials will be replaced.")
                print()
                confirm = input("Continue with new registration? (y/n) [y]: ").lower().strip()
                if confirm == '' or confirm == 'y':
                    break
                print()
                return None

            print()
            print("❌ Invalid choice. Please enter 1 or 2.")
            print()
    else:
        # No credentials, must register
        print("No Moltbook credentials found. Registration required.")
        print()

    # Registration flow - keep trying until success or user gives up
    while True:
        # Get agent info
        print()
        print("-" * 60)
        print("Step 1: Agent Information")
        print("-" * 60)

        agent_info = get_agent_info()
        if not agent_info:
            # User cancelled at confirmation
            print()
            print("You can:")
            print("  • Try again with different information")
            print("  • Exit setup (you'll need to register later)")
            print()
            retry = input("Try again? (y/n): ").lower().strip()
            if retry != 'y':
                print()
                print("❌ Registration cancelled.")
                print()
                print("TinyMolty requires a Moltbook account to function.")
                print("To register later, run: uv run tinymolty --setup")
                print()
                import sys
                sys.exit(0)
            continue  # Go back to get_agent_info

        name, description = agent_info

        # Try to register
        print()
        print("-" * 60)
        print("Step 2: Creating Moltbook Account")
        print("-" * 60)

        result = asyncio.run(
            register_agent_cli(
                name,
                description,
                credentials_path=credentials_path,
            )
        )
        if result:
            # Success!
            return result
        else:
            # Registration failed (error details already printed)
            print()
            print("You can:")
            print("  • Try again (maybe with a different agent name)")
            print("  • Exit and retry later")
            print()
            retry = input("Try again? (y/n): ").lower().strip()
            if retry != 'y':
                print()
                print("❌ Registration cancelled.")
                print()
                print("TinyMolty requires a Moltbook account to function.")
                print("To register later, run: uv run tinymolty --setup")
                print()
                print("Tip: Set DEBUG=1 environment variable for detailed error info")
                print()
                import sys
                sys.exit(0)
            # Loop back to try again
