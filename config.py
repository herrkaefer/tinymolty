from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import keyring
from pydantic import BaseModel, Field, ValidationError, field_validator


DEFAULT_CONFIG_PATH = Path("~/.config/tinymolty/config.toml").expanduser()
KEYRING_SERVICE = "tinymolty"


class BotConfig(BaseModel):
    name: str = "CuriousMolty"
    description: str = "A curious AI agent exploring moltbook"


class UIConfig(BaseModel):
    mode: Literal["terminal", "telegram"] = "terminal"


class PersonalityConfig(BaseModel):
    system_prompt: str = "You are CuriousMolty, a thoughtful AI agent on Moltbook."
    topics_of_interest: list[str] = Field(default_factory=list)


class LLMConfig(BaseModel):
    provider: Literal["openai", "gemini", "openrouter"] = "openai"
    model: str = "gpt-4o-mini"
    api_key: str = "keyring"
    temperature: float = 0.8

    @field_validator("temperature")
    @classmethod
    def _temp_range(cls, value: float) -> float:
        if not 0 <= value <= 2:
            raise ValueError("temperature must be between 0 and 2")
        return value


class MoltbookConfig(BaseModel):
    credentials_path: str = "~/.config/moltbook/credentials.json"


class TelegramConfig(BaseModel):
    enabled: bool = False
    bot_token: str = "keyring"
    chat_id: str = ""


class BehaviorConfig(BaseModel):
    enabled_actions: list[str] = Field(
        default_factory=lambda: ["post"]
    )
    post_cooldown_minutes: int = 60
    comment_cooldown_minutes: int = 5
    browse_interval_minutes: int = 15
    heartbeat_interval_hours: int = 4
    max_comments_per_day: int = 30
    max_posts_per_day: int = 10
    preferred_submolts: list[str] = Field(default_factory=list)


class AdvancedConfig(BaseModel):
    log_level: str = "INFO"
    jitter_range_seconds: tuple[int, int] = (5, 30)


class AppConfig(BaseModel):
    bot: BotConfig = Field(default_factory=BotConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    personality: PersonalityConfig = Field(default_factory=PersonalityConfig)
    llm: LLMConfig = Field(default_factory=LLMConfig)
    moltbook: MoltbookConfig = Field(default_factory=MoltbookConfig)
    telegram: TelegramConfig = Field(default_factory=TelegramConfig)
    behavior: BehaviorConfig = Field(default_factory=BehaviorConfig)
    advanced: AdvancedConfig = Field(default_factory=AdvancedConfig)


@dataclass(slots=True)
class ResolvedSecrets:
    llm_api_key: str | None
    telegram_token: str | None


def get_default_config_path() -> Path:
    return DEFAULT_CONFIG_PATH


def _expand_path(value: str) -> str:
    return str(Path(value).expanduser())


def ensure_config_permissions(path: Path) -> None:
    try:
        if path.exists():
            path.chmod(0o600)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch(mode=0o600, exist_ok=True)
    except OSError:
        return


def resolve_secret(value: str, key_name: str) -> str | None:
    if not value:
        return None
    if value == "keyring":
        return keyring.get_password(KEYRING_SERVICE, key_name)
    if value.startswith("env:"):
        env_key = value.split("env:", 1)[1]
        return os.getenv(env_key)
    return value


def store_secret(value: str, key_name: str, storage: str) -> str:
    if storage == "keyring":
        keyring.set_password(KEYRING_SERVICE, key_name, value)
        return "keyring"
    if storage.startswith("env:"):
        return storage
    return value


def resolve_secrets(config: AppConfig) -> ResolvedSecrets:
    return ResolvedSecrets(
        llm_api_key=resolve_secret(config.llm.api_key, "llm_api_key"),
        telegram_token=resolve_secret(config.telegram.bot_token, "telegram_bot_token"),
    )


def validate_config(config: AppConfig, resolved: ResolvedSecrets | None = None) -> None:
    if config.ui.mode == "telegram":
        if not config.telegram.enabled:
            raise ValueError("telegram.enabled must be true when ui.mode = telegram")
        if not config.telegram.chat_id:
            raise ValueError("telegram.chat_id is required for telegram UI")
        if resolved and not resolved.telegram_token:
            raise ValueError("telegram bot token is missing")
    if resolved and not resolved.llm_api_key:
        raise ValueError("LLM api key is missing")


def load_config(path: Path | None = None) -> AppConfig:
    import tomllib

    config_path = path or get_default_config_path()
    if not config_path.exists():
        raise FileNotFoundError(str(config_path))
    data = tomllib.loads(config_path.read_text())
    data.setdefault("moltbook", {})
    data["moltbook"]["credentials_path"] = _expand_path(
        data["moltbook"].get("credentials_path", "~/.config/moltbook/credentials.json")
    )
    config = AppConfig.model_validate(data)
    return config


def save_config(config: AppConfig, path: Path | None = None) -> Path:
    import tomli_w

    config_path = path or get_default_config_path()
    ensure_config_permissions(config_path)
    config_path.write_text(tomli_w.dumps(config.model_dump()))
    ensure_config_permissions(config_path)
    return config_path


def try_load_config(path: Path | None = None) -> tuple[AppConfig | None, str | None]:
    try:
        return load_config(path), None
    except FileNotFoundError:
        return None, "missing"
    except ValidationError as exc:
        return None, str(exc)
    except Exception as exc:  # pragma: no cover - fallback for unexpected errors
        return None, str(exc)
