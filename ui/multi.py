from __future__ import annotations

import asyncio

from .base import UserInterface


class MultiUI(UserInterface):
    def __init__(self, primary: UserInterface, secondary: UserInterface | None = None) -> None:
        self.primary = primary
        self.secondary = secondary

    async def start(self) -> None:
        import sys
        print(f"[MultiUI] Starting primary UI...", file=sys.stderr, flush=True)
        await self.primary.start()
        print(f"[MultiUI] Primary UI started", file=sys.stderr, flush=True)
        if self.secondary:
            print(f"[MultiUI] Starting secondary UI (Telegram)...", file=sys.stderr, flush=True)
            try:
                await self.secondary.start()
                print(f"[MultiUI] Secondary UI started", file=sys.stderr, flush=True)
            except Exception as exc:
                print(f"[MultiUI] ❌ Secondary start failed: {exc}", file=sys.stderr, flush=True)
                await self.primary.send_status(f"⚠️ Telegram start failed: {type(exc).__name__}: {exc}")
        else:
            print(f"[MultiUI] No secondary UI", file=sys.stderr, flush=True)

    async def stop(self) -> None:
        await self.primary.stop()
        if self.secondary:
            try:
                await self.secondary.stop()
            except Exception as exc:
                await self.primary.send_status(f"⚠️ Telegram stop failed: {type(exc).__name__}: {exc}")

    async def send_status(self, message: str) -> None:
        await self.primary.send_status(message)
        if self.secondary:
            try:
                await self.secondary.send_status(message)
            except Exception as exc:
                await self.primary.send_status(f"⚠️ Telegram send failed: {type(exc).__name__}: {exc}")

    async def prompt(self, message: str) -> str:
        if self.secondary:
            await self.secondary.send_status(message)
        return await self.primary.prompt(message)

    async def get_command(self) -> str | None:
        if self.secondary:
            cmd = await self.secondary.get_command()
            if cmd:
                return cmd
        return await self.primary.get_command()

    def get_command_sync(self) -> str | None:
        if self.secondary and hasattr(self.secondary, "get_command_sync"):
            cmd = self.secondary.get_command_sync()
            if cmd:
                return cmd
        if hasattr(self.primary, "get_command_sync"):
            return self.primary.get_command_sync()
        return None

    async def update_activity(self, message: str, next_action_seconds: float | None = None) -> None:
        await self.primary.update_activity(message, next_action_seconds)
        if self.secondary:
            try:
                await self.secondary.update_activity(message, next_action_seconds)
            except Exception as exc:
                await self.primary.send_status(f"⚠️ Telegram update failed: {type(exc).__name__}: {exc}")

    def set_agent_info(self, agent_name: str, profile_url: str | None, owner_name: str = "") -> None:
        if hasattr(self.primary, "set_agent_info"):
            try:
                self.primary.set_agent_info(agent_name, profile_url, owner_name)
            except Exception:
                pass
        if self.secondary and hasattr(self.secondary, "set_agent_info"):
            try:
                self.secondary.set_agent_info(agent_name, profile_url, owner_name)
            except Exception:
                pass


class FilteredUI(UserInterface):
    def __init__(self, inner: UserInterface, should_send: callable) -> None:
        self.inner = inner
        self.should_send = should_send

    async def start(self) -> None:
        await self.inner.start()

    async def stop(self) -> None:
        await self.inner.stop()

    async def send_status(self, message: str) -> None:
        if self.should_send(message):
            await self.inner.send_status(message)

    async def prompt(self, message: str) -> str:
        if self.should_send(message):
            await self.inner.send_status(message)
        return await self.inner.prompt(message)

    async def get_command(self) -> str | None:
        return await self.inner.get_command()

    async def update_activity(self, message: str, next_action_seconds: float | None = None) -> None:
        if self.should_send(message):
            await self.inner.update_activity(message, next_action_seconds)
