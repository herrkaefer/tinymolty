from __future__ import annotations

import asyncio
import random
from datetime import datetime, timedelta

from config import AdvancedConfig, BehaviorConfig


class Scheduler:
    def __init__(self, behavior: BehaviorConfig, advanced: AdvancedConfig) -> None:
        self.behavior = behavior
        self.advanced = advanced
        self._last_action: dict[str, datetime] = {}
        self._daily_counts: dict[str, tuple[datetime.date, int]] = {}

    def _cooldown_seconds(self, action: str) -> int:
        if action == "post":
            return self.behavior.post_cooldown_minutes * 60
        if action == "comment":
            return self.behavior.comment_cooldown_minutes * 60
        if action == "browse":
            return self.behavior.browse_interval_minutes * 60
        if action == "heartbeat":
            return self.behavior.heartbeat_interval_hours * 3600
        return 0

    def _max_per_day(self, action: str) -> int | None:
        if action == "comment":
            return self.behavior.max_comments_per_day
        if action == "post":
            return self.behavior.max_posts_per_day
        return None

    def _ensure_daily_bucket(self, action: str) -> int:
        today = datetime.utcnow().date()
        day, count = self._daily_counts.get(action, (today, 0))
        if day != today:
            count = 0
        self._daily_counts[action] = (today, count)
        return count

    def can_do(self, action: str) -> bool:
        if action not in self.behavior.enabled_actions:
            return False
        last = self._last_action.get(action)
        if last:
            cooldown = timedelta(seconds=self._cooldown_seconds(action))
            if datetime.utcnow() - last < cooldown:
                return False
        max_per_day = self._max_per_day(action)
        if max_per_day is not None:
            count = self._ensure_daily_bucket(action)
            if count >= max_per_day:
                return False
        return True

    def record_action(self, action: str) -> None:
        self._last_action[action] = datetime.utcnow()
        max_per_day = self._max_per_day(action)
        if max_per_day is not None:
            day, count = self._daily_counts.get(action, (datetime.utcnow().date(), 0))
            self._daily_counts[action] = (day, count + 1)

    def next_available_in(self, action: str) -> float:
        last = self._last_action.get(action)
        if not last:
            return 0.0
        cooldown = self._cooldown_seconds(action)
        remaining = cooldown - (datetime.utcnow() - last).total_seconds()
        return max(0.0, remaining)

    def jitter(self) -> float:
        low, high = self.advanced.jitter_range_seconds
        return random.uniform(low, high)

    async def sleep_with_jitter(self, base_seconds: float) -> None:
        await asyncio.sleep(base_seconds + self.jitter())
