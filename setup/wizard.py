"""
TinyMolty setup wizard
Simple command-line configuration interface
"""
from __future__ import annotations

from pathlib import Path

from config import (
    AppConfig,
    BotConfig,
    LLMConfig,
    MoltbookConfig,
    PersonalityConfig,
    TelegramConfig,
    UIConfig,
    BehaviorConfig,
    ensure_config_permissions,
    save_config,
    store_secret,
)


def print_section(title: str):
    """Print a section header"""
    print()
    print("-" * 60)
    print(f"  {title}")
    print("-" * 60)


def get_ui_mode() -> str:
    """Get UI mode from user"""
    print_section("UI Mode")
    print("How do you want to interact with TinyMolty?")
    print("  1. Terminal (run in your terminal)")
    print("  2. Telegram (receive updates via Telegram)")
    print()

    while True:
        choice = input("Enter choice (1 or 2) [1]: ").strip() or "1"
        if choice == "1":
            return "terminal"
        elif choice == "2":
            return "telegram"
        print("Invalid choice. Please enter 1 or 2.")


def get_bot_config(default_name: str = "CuriousMolty", default_desc: str = "A curious AI agent exploring moltbook") -> BotConfig:
    """Get bot configuration from user"""
    print_section("Bot Information")

    print("This is the name TinyMolty will use in its configuration.")
    print("(Usually the same as your Moltbook agent name)")
    print()

    name = input(f"Bot name [{default_name}]: ").strip() or default_name
    description = input(f"Bot description [{default_desc}]: ").strip() or default_desc

    return BotConfig(name=name, description=description)


def get_personality_config() -> PersonalityConfig:
    """Get personality configuration from user"""
    print_section("Personality")

    print("System prompt (defines your bot's personality):")
    default_prompt = "You are CuriousMolty, a thoughtful AI agent on Moltbook."
    system_prompt = input(f"[{default_prompt}]: ").strip() or default_prompt

    print()
    print("Topics of interest (comma-separated):")
    topics_input = input("[AI ethics, philosophy, open source]: ").strip()
    if topics_input:
        topics = [t.strip() for t in topics_input.split(",") if t.strip()]
    else:
        topics = ["AI ethics", "philosophy", "open source"]

    return PersonalityConfig(system_prompt=system_prompt, topics_of_interest=topics)


def get_llm_config() -> LLMConfig:
    """Get LLM configuration from user"""
    print_section("LLM Configuration")

    # Provider
    print("LLM Provider:")
    print("  1. OpenAI")
    print("  2. Google Gemini")
    print("  3. OpenRouter")
    print()

    while True:
        choice = input("Enter choice (1-3) [1]: ").strip() or "1"
        if choice == "1":
            provider = "openai"
            default_model = "gpt-4o-mini"
            break
        elif choice == "2":
            provider = "gemini"
            default_model = "gemini-pro"
            break
        elif choice == "3":
            provider = "openrouter"
            default_model = "openai/gpt-4o-mini"
            break
        print("Invalid choice. Please enter 1, 2, or 3.")

    # Model
    print()
    model = input(f"Model name [{default_model}]: ").strip() or default_model

    # API Key
    print()
    print("API Key (your input will be hidden):")
    from getpass import getpass
    api_key = getpass("Enter API key: ").strip()

    while not api_key:
        print("API key cannot be empty.")
        api_key = getpass("Enter API key: ").strip()

    # Storage method
    print()
    print("How to store the API key:")
    print("  1. Keyring (system keyring - recommended)")
    print("  2. Environment variable")
    print("  3. Plain text in config (not recommended)")
    print()

    while True:
        storage_choice = input("Enter choice (1-3) [1]: ").strip() or "1"
        if storage_choice == "1":
            storage = "keyring"
            break
        elif storage_choice == "2":
            storage = "env:TINYMOLTY_LLM_API_KEY"
            break
        elif storage_choice == "3":
            storage = "direct"
            break
        print("Invalid choice. Please enter 1, 2, or 3.")

    # Store the key
    api_key_ref = store_secret(api_key, "llm_api_key", storage)

    # Temperature
    print()
    while True:
        temp_input = input("Temperature (0.0-2.0) [0.8]: ").strip() or "0.8"
        try:
            temperature = float(temp_input)
            if 0 <= temperature <= 2:
                break
            print("Temperature must be between 0 and 2.")
        except ValueError:
            print("Invalid number. Please try again.")

    return LLMConfig(
        provider=provider,
        model=model,
        api_key=api_key_ref,
        temperature=temperature
    )


def get_telegram_config(ui_mode: str) -> TelegramConfig:
    """Get Telegram configuration from user"""
    print_section("Telegram Configuration")

    if ui_mode == "terminal":
        print("Enable Telegram notifications? (optional)")
        enable = input("Enable Telegram? (y/n) [n]: ").strip().lower() == 'y'
    else:
        print("Telegram is required for Telegram UI mode.")
        enable = True

    if not enable:
        return TelegramConfig(enabled=False, bot_token="keyring", chat_id="")

    print()
    print("Bot token (your input will be hidden):")
    from getpass import getpass
    bot_token = getpass("Enter Telegram bot token: ").strip()

    print()
    chat_id = input("Chat ID: ").strip()

    # Store token in keyring
    if bot_token:
        token_ref = store_secret(bot_token, "telegram_bot_token", "keyring")
    else:
        token_ref = "keyring"

    return TelegramConfig(enabled=enable, bot_token=token_ref, chat_id=chat_id)


def get_moltbook_config() -> MoltbookConfig:
    """Get Moltbook configuration from user"""
    print_section("Moltbook Configuration")

    default_path = "~/.config/moltbook/credentials.json"
    path = input(f"Credentials path [{default_path}]: ").strip() or default_path

    return MoltbookConfig(credentials_path=path)


def run_configuration_wizard(registration_data: dict | None = None) -> AppConfig:
    """Run the interactive configuration wizard"""
    print()
    print("=" * 60)
    print("  TinyMolty Setup Wizard")
    print("=" * 60)
    print()
    print("Let's configure your TinyMolty bot!")
    print()

    # Extract defaults from registration data if available
    default_name = "CuriousMolty"
    default_desc = "A curious AI agent exploring moltbook"

    if registration_data:
        # New registration - use the just-registered agent name
        default_name = registration_data.get("agent_name", default_name)
    else:
        # Using existing credentials - try to load agent name from credentials
        try:
            from moltbook.registration import load_credentials
            creds = load_credentials()
            if creds and "agent_name" in creds:
                default_name = creds["agent_name"]
        except Exception:
            # If we can't load credentials, use generic default
            pass

    # Collect configuration
    ui_mode = get_ui_mode()
    bot_config = get_bot_config(default_name=default_name, default_desc=default_desc)
    personality_config = get_personality_config()
    llm_config = get_llm_config()
    moltbook_config = get_moltbook_config()
    telegram_config = get_telegram_config(ui_mode)

    # Create config
    config = AppConfig(
        bot=bot_config,
        ui=UIConfig(mode=ui_mode),
        personality=personality_config,
        llm=llm_config,
        moltbook=moltbook_config,
        telegram=telegram_config,
        behavior=BehaviorConfig(),  # Use defaults
    )

    # Summary
    print()
    print("=" * 60)
    print("  Configuration Summary")
    print("=" * 60)
    print(f"Bot Name: {config.bot.name}")
    print(f"UI Mode: {config.ui.mode}")
    print(f"LLM Provider: {config.llm.provider}")
    print(f"LLM Model: {config.llm.model}")
    print(f"Topics: {', '.join(config.personality.topics_of_interest)}")
    if config.telegram.enabled:
        print(f"Telegram: Enabled")
    print("=" * 60)
    print()

    return config


def run_setup(config_path: Path | None = None) -> AppConfig:
    """Run the complete setup process"""
    # Step 1: Handle Moltbook account registration
    from pathlib import Path as P
    moltbook_cred_path = P("~/.config/moltbook/credentials.json").expanduser()

    print("🦀 Welcome to TinyMolty!")
    print()

    credentials_exist = moltbook_cred_path.exists()

    if credentials_exist:
        # Show existing account info
        try:
            import json
            from moltbook.registration import load_credentials
            creds = load_credentials()
            if creds:
                print("✓ Found existing Moltbook account:")
                print(f"  Agent: {creds.get('agent_name', 'Unknown')}")
                print()
        except Exception:
            pass

    try:
        from setup.registration_wizard import run_registration_wizard
        registration_data = run_registration_wizard(credentials_exist=credentials_exist)

        if registration_data:
            print()
            input("Press Enter to continue with TinyMolty configuration...")
        else:
            # User chose to use existing credentials (only possible if credentials_exist)
            print()
    except SystemExit:
        # User cancelled during registration
        raise
    except Exception as e:
        print()
        print(f"❌ Registration wizard error: {e}")
        print()
        print("You can try again by running: uv run tinymolty --setup")
        import sys
        sys.exit(1)

    # Step 2: Run main configuration wizard
    config = run_configuration_wizard(registration_data=registration_data)

    # Save configuration
    path = config_path
    saved_path = save_config(config, path)
    ensure_config_permissions(saved_path)

    print()
    print(f"✅ Configuration saved to: {saved_path}")
    print()
    print("=" * 60)
    print("  Behavior Settings (Using Defaults)")
    print("=" * 60)
    print(f"Heartbeat interval: {config.behavior.heartbeat_interval_hours} hours")
    print(f"Browse interval: {config.behavior.browse_interval_minutes} minutes")
    print(f"Post cooldown: {config.behavior.post_cooldown_minutes} minutes")
    print(f"Comment cooldown: {config.behavior.comment_cooldown_minutes} minutes")
    print(f"Max posts per day: {config.behavior.max_posts_per_day}")
    print(f"Max comments per day: {config.behavior.max_comments_per_day}")
    print(f"Enabled actions: {', '.join(config.behavior.enabled_actions)}")
    print()
    print(f"To customize these settings, edit: {saved_path}")
    print(f"Then modify the [behavior] section")
    print("=" * 60)
    print()

    return config
