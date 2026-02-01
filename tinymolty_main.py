"""
TinyMolty main entry point module
This module provides the main() function for the CLI script
"""
from __future__ import annotations

import argparse
from pathlib import Path

from app import run
from config import (
    resolve_secrets,
    try_load_config,
    validate_config,
)
from setup import run_setup


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="TinyMolty - Moltbook AI agent bot")
    parser.add_argument("--setup", action="store_true", help="Run setup wizard")
    parser.add_argument("--config", type=str, help="Path to config TOML")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config_path = Path(args.config).expanduser() if args.config else None
    if args.setup:
        config = run_setup(config_path)
    else:
        config, error = try_load_config(config_path)
        if config is None:
            if error != "missing":
                print(f"Config invalid: {error}")
            config = run_setup(config_path)
    secrets = resolve_secrets(config)
    validate_config(config, secrets)
    run(config, secrets)


if __name__ == "__main__":
    main()
