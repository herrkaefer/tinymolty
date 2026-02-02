from __future__ import annotations

from abc import ABC, abstractmethod


class UserInterface(ABC):
    @abstractmethod
    async def start(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def stop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def send_status(self, message: str) -> None:
        """Send detailed status message (to all UIs)"""
        raise NotImplementedError

    async def send_summary(self, message: str) -> None:
        """Send summary message (optional, for Telegram etc.)

        Default implementation does nothing. Override in specific UIs if needed.
        This is used to send concise summaries to Telegram while keeping
        detailed logs in the terminal.
        """
        pass

    @abstractmethod
    async def prompt(self, message: str) -> str:
        raise NotImplementedError

    @abstractmethod
    async def get_command(self) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def update_activity(self, message: str, next_action_seconds: float | None = None) -> None:
        raise NotImplementedError
