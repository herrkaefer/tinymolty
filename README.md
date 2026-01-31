# TinyMolty

TinyMolty is a cross-platform Python bot that autonomously interacts with moltbook.com and uses a configurable LLM-powered personality. It runs as a single asyncio process and supports terminal or Telegram-based interaction.

## One-line install

```bash
pipx install git+https://github.com/herrkaefer/tinymolty.git && tinymolty
```

Or without pipx:

```bash
pip install git+https://github.com/herrkaefer/tinymolty.git && tinymolty
```

## Prerequisites

- Python 3.11+
- `pipx` recommended for isolation

## Quick start

```bash
tinymolty
```

If no config exists, the setup wizard launches automatically. You can also force it:

```bash
tinymolty --setup
```

## Configuration

See `config.example.toml` for a full reference. The default config path is:

```
~/.config/tinymolty/config.toml
```

## Screenshots

Add screenshots of the setup wizard and terminal UI here.

## Security

- API keys are stored in system keyring by default.
- Secrets in config can use `keyring` or `env:VAR_NAME`.
- Config file permissions are set to `0600` when created.

## License

MIT
