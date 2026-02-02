from .base import UserInterface
try:
    from .tui_app import TinyMoltyApp
except ModuleNotFoundError as exc:
    if exc.name != "textual":
        raise
    TinyMoltyApp = None  # type: ignore[assignment]

__all__ = ["UserInterface", "TinyMoltyApp"]
