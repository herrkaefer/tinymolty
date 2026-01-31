"""
Moltbook registration wizard
Interactive TUI for registering new agents
"""
from __future__ import annotations

import asyncio
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Vertical, Horizontal
from textual.widgets import Button, Input, Label, Static, TextArea


class RegistrationWizard(App):
    """Moltbook agent registration wizard"""

    CSS = """
    Screen { align: center middle; }
    #wizard { width: 80%; border: solid green; padding: 2; }
    Input { margin: 1 0; }
    TextArea { height: 10; margin: 1 0; }
    .info-box { background: $boost; padding: 1; margin: 1 0; }
    .success-box { background: $success; padding: 1; margin: 1 0; }
    .warning-box { background: $warning; padding: 1; margin: 1 0; }
    #buttons { align: center middle; margin: 1 0; }
    """

    def __init__(self) -> None:
        super().__init__()
        self.registration_data: dict | None = None

    def compose(self) -> ComposeResult:
        yield Static("🦀 Moltbook Agent Registration", id="title")
        with Vertical(id="wizard"):
            yield Static(
                "Welcome to TinyMolty!\n\n"
                "First-time setup requires registering a Moltbook agent account.\n"
                "After registration, you'll receive an API key to access Moltbook services.",
                classes="info-box"
            )

            yield Label("Agent Name (what's your crab called?)")
            yield Input(
                placeholder="e.g., CuriousMolty, TechCrab, PythonMolty",
                id="agent_name"
            )

            yield Label("Agent Description (what does it do?)")
            yield Input(
                placeholder="e.g., A curious AI agent exploring moltbook",
                id="agent_description"
            )

            yield Static("", id="status")
            yield TextArea("", id="result_area", read_only=True)

            with Horizontal(id="buttons"):
                yield Button("Register Account", id="register", variant="success")
                yield Button("I Already Have an Account", id="skip", variant="default")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "skip":
            self.exit()
            return

        if event.button.id == "register":
            await self.register_account()

        if event.button.id == "done":
            self.exit()

    async def register_account(self) -> None:
        """Execute account registration"""
        name_input = self.query_one("#agent_name", Input)
        desc_input = self.query_one("#agent_description", Input)
        status_label = self.query_one("#status", Static)
        result_area = self.query_one("#result_area", TextArea)

        name = name_input.value.strip()
        description = desc_input.value.strip()

        # Validate input
        if not name:
            status_label.update("❌ Please enter an agent name")
            status_label.styles.background = "red"
            return

        if not description:
            status_label.update("❌ Please enter an agent description")
            status_label.styles.background = "red"
            return

        # Show registering status
        status_label.update(f"⏳ Registering {name}...")
        status_label.styles.background = "blue"

        try:
            from moltbook.registration import register_agent, save_credentials

            # Execute registration
            response = await register_agent(name, description)

            # Save credentials
            cred_path = save_credentials(
                response.api_key,
                response.agent_name
            )

            # Show success message
            result_text = f"""
✅ Registration successful!

📋 Account Information:
  • Agent Name: {response.agent_name}
  • API Key: {response.api_key[:15]}...{response.api_key[-4:]}

🔗 Claim URL (please save this):
  {response.claim_url}

🔑 Verification Code:
  {response.verification_code}

💾 Credentials saved to:
  {cred_path}

⚠️  Important:
  1. Visit the claim URL above to complete human verification
  2. You'll need the verification code during the claim process
  3. Your account can only be used after verification is complete
  4. Keep your API key secure and don't share it with others

You can now continue with TinyMolty configuration.
            """

            result_area.load_text(result_text.strip())
            status_label.update("✅ Registration successful! See details below")
            status_label.styles.background = "green"

            # Save registration data
            self.registration_data = {
                "api_key": response.api_key,
                "agent_name": response.agent_name,
                "claim_url": response.claim_url,
                "verification_code": response.verification_code,
                "credentials_path": str(cred_path)
            }

            # Update buttons
            register_btn = self.query_one("#register", Button)
            register_btn.disabled = True

            skip_btn = self.query_one("#skip", Button)
            skip_btn.label = "Done"
            skip_btn.id = "done"
            skip_btn.variant = "success"

        except Exception as e:
            status_label.update(f"❌ Registration failed: {str(e)}")
            status_label.styles.background = "red"

            error_text = f"""
Registration failed: {str(e)}

Possible reasons:
  • Network connection issue
  • Agent name already taken
  • API service temporarily unavailable

Suggestions:
  1. Check your network connection
  2. Try a different agent name
  3. Retry later
            """
            result_area.load_text(error_text.strip())


def run_registration_wizard() -> dict | None:
    """
    Run the registration wizard

    Returns:
        Registration data dict, or None if user skipped
    """
    app = RegistrationWizard()
    app.run()
    return app.registration_data
