from __future__ import annotations

import asyncio
import time


class TokenBucket:
    def __init__(self, capacity: int, refill_per_second: float) -> None:
        self.capacity = capacity
        self.refill_per_second = refill_per_second
        self.tokens = float(capacity)
        self.updated_at = time.monotonic()
        self._lock = asyncio.Lock()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self.updated_at
        if elapsed <= 0:
            return
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_second)
        self.updated_at = now

    async def acquire(self, tokens: float = 1.0) -> None:
        async with self._lock:
            while True:
                self._refill()
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return
                missing = tokens - self.tokens
                wait_time = max(missing / self.refill_per_second, 0.1)
                await asyncio.sleep(wait_time)


class RateLimiter:
    def __init__(self, requests_per_minute: int = 100) -> None:
        self.global_bucket = TokenBucket(
            capacity=requests_per_minute, refill_per_second=requests_per_minute / 60.0
        )

    async def wait(self) -> None:
        await self.global_bucket.acquire(1.0)
