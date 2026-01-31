import os
import tempfile
import unittest
from pathlib import Path

from config import (
    AppConfig,
    TelegramConfig,
    UIConfig,
    resolve_secrets,
    save_config,
    load_config,
    validate_config,
)


class ConfigTests(unittest.TestCase):
    def test_config_roundtrip(self):
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
        secrets = resolve_secrets(config)
        self.assertEqual(secrets.llm_api_key, "test-key")

    def test_validate_config_telegram_requirements(self):
        config = AppConfig(ui=UIConfig(mode="telegram"), telegram=TelegramConfig(enabled=False))
        with self.assertRaises(ValueError):
            validate_config(config)
