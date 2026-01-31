from __future__ import annotations

from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.widgets import Button, Input, Label, Select, Static, Switch

from config import (
    AppConfig,
    BotConfig,
    LLMConfig,
    MoltbookConfig,
    PersonalityConfig,
    TelegramConfig,
    UIConfig,
    ensure_config_permissions,
    save_config,
    store_secret,
)


class WizardApp(App):
    CSS = """
    Screen { align: center middle; }
    #wizard { width: 80%; }
    Input, Select { margin: 1 0; }
    """

    def __init__(self, config_path: Path | None = None) -> None:
        super().__init__()
        self.config_path = config_path
        self.config: AppConfig | None = None

    def compose(self) -> ComposeResult:
        yield Static("TinyMolty Setup Wizard", id="title")
        with Vertical(id="wizard"):
            yield Label("UI Mode")
            yield Select([("Terminal", "terminal"), ("Telegram", "telegram")], value="terminal", id="ui_mode")
            yield Label("Bot Name")
            yield Input(value="CuriousMolty", id="bot_name")
            yield Label("Bot Description")
            yield Input(value="A curious AI agent exploring moltbook", id="bot_description")
            yield Label("System Prompt")
            yield Input(value="You are CuriousMolty, a thoughtful AI agent on Moltbook.", id="system_prompt")
            yield Label("Topics of Interest (comma separated)")
            yield Input(value="AI ethics, philosophy, open source", id="topics")
            yield Label("LLM Provider")
            yield Select(
                [("OpenAI", "openai"), ("Gemini", "gemini"), ("OpenRouter", "openrouter")],
                value="openai",
                id="llm_provider",
            )
            yield Label("LLM Model")
            yield Input(value="gpt-4o-mini", id="llm_model")
            yield Label("LLM API Key (masked)")
            yield Input(password=True, id="llm_api_key")
            yield Label("Key Storage")
            yield Select(
                [("Keyring", "keyring"), ("Environment Variable", "env:TINYMOLTY_LLM_API_KEY"), ("Plaintext", "direct")],
                value="keyring",
                id="llm_storage",
            )
            yield Label("Moltbook Credentials Path")
            yield Input(value="~/.config/moltbook/credentials.json", id="moltbook_path")
            yield Label("Enable Telegram")
            yield Switch(value=False, id="telegram_enabled")
            yield Label("Telegram Bot Token (masked)")
            yield Input(password=True, id="telegram_token")
            yield Label("Telegram Chat ID")
            yield Input(value="", id="telegram_chat")
            yield Button("Save & Exit", id="save", variant="success")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "save":
            return
        ui_mode = self.query_one("#ui_mode", Select).value or "terminal"
        bot_name = self.query_one("#bot_name", Input).value
        bot_description = self.query_one("#bot_description", Input).value
        system_prompt = self.query_one("#system_prompt", Input).value
        topics_raw = self.query_one("#topics", Input).value
        topics = [item.strip() for item in topics_raw.split(",") if item.strip()]
        llm_provider = self.query_one("#llm_provider", Select).value or "openai"
        llm_model = self.query_one("#llm_model", Input).value
        llm_api_key = self.query_one("#llm_api_key", Input).value
        llm_storage = self.query_one("#llm_storage", Select).value or "keyring"
        moltbook_path = self.query_one("#moltbook_path", Input).value
        telegram_enabled = self.query_one("#telegram_enabled", Switch).value
        telegram_token = self.query_one("#telegram_token", Input).value
        telegram_chat = self.query_one("#telegram_chat", Input).value

        llm_api_key_ref = (
            store_secret(llm_api_key, "llm_api_key", llm_storage)
            if llm_api_key
            else llm_storage
        )
        telegram_token_ref = (
            store_secret(telegram_token, "telegram_bot_token", "keyring")
            if telegram_token and telegram_enabled
            else "keyring"
        )

        self.config = AppConfig(
            bot=BotConfig(name=bot_name, description=bot_description),
            ui=UIConfig(mode=ui_mode),
            personality=PersonalityConfig(
                system_prompt=system_prompt, topics_of_interest=topics
            ),
            llm=LLMConfig(provider=llm_provider, model=llm_model, api_key=llm_api_key_ref),
            moltbook=MoltbookConfig(credentials_path=moltbook_path),
            telegram=TelegramConfig(
                enabled=telegram_enabled,
                bot_token=telegram_token_ref,
                chat_id=telegram_chat,
            ),
        )
        self.exit()


def run_setup(config_path: Path | None = None) -> AppConfig:
    # Step 1: Check if Moltbook account registration is needed
    from pathlib import Path as P
    moltbook_cred_path = P("~/.config/moltbook/credentials.json").expanduser()

    if not moltbook_cred_path.exists():
        print("🦀 Welcome to TinyMolty!")
        print()
        print("First-time setup detected. Moltbook account registration required.")
        print("Opening registration wizard...")
        print()

        try:
            from setup.registration_wizard import run_registration_wizard
            registration_data = run_registration_wizard()

            if registration_data:
                print()
                print("=" * 60)
                print("✅ Moltbook Account Registration Successful!")
                print("=" * 60)
                print(f"Agent Name: {registration_data['agent_name']}")
                print(f"API Key: {registration_data['api_key'][:15]}...")
                print()
                print("⚠️  Important:")
                print(f"Please visit the following URL to complete human verification:")
                print(f"  {registration_data['claim_url']}")
                print()
                print(f"Verification Code: {registration_data['verification_code']}")
                print()
                print("=" * 60)
                print()
                input("Press Enter to continue with TinyMolty configuration...")
            else:
                print()
                print("Registration skipped. Please ensure you have Moltbook credentials.")
                print()
        except Exception as e:
            print(f"Registration wizard error: {e}")
            print("You can register manually later or use existing credentials.")

    # Step 2: Run main configuration wizard
    app = WizardApp(config_path)
    app.run()
    if app.config is None:
        raise RuntimeError("Setup wizard aborted.")
    path = config_path
    saved_path = save_config(app.config, path)
    ensure_config_permissions(saved_path)
    return app.config
