import os
import tempfile
import unittest
from pathlib import Path

from config import (
    AppConfig,
    TelegramConfig,
    resolve_secrets,
    save_config,
    load_config,
    validate_config,
)

try:
    import tomli_w  # type: ignore
except ModuleNotFoundError:
    tomli_w = None


class ConfigTests(unittest.TestCase):
    def test_config_roundtrip(self):
        if tomli_w is None:
            self.skipTest("tomli_w not installed")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "config.toml"
            config = AppConfig()
            save_config(config, path)
            loaded = load_config(path)
            self.assertEqual(loaded.bot.name, config.bot.name)
            self.assertEqual(loaded.llm.provider, config.llm.provider)

    def test_resolve_secrets_env(self):
        os.environ["TINYMOLTY_LLM_API_KEY"] = "test-key"
        config = AppConfig()
        config.llm.api_key = "env:TINYMOLTY_LLM_API_KEY"
        config.telegram.bot_token = ""
        secrets = resolve_secrets(config)
        self.assertEqual(secrets.llm_api_key, "test-key")

    def test_validate_config_telegram_requirements(self):
        config = AppConfig(telegram=TelegramConfig(enabled=True, bot_token="", chat_id=""))
        secrets = resolve_secrets(config)
        with self.assertRaises(ValueError):
            validate_config(config, secrets)
