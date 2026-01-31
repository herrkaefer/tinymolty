from __future__ import annotations

import asyncio
import json
import random
from typing import Iterable

from config import AppConfig
from llm.base import LLMProvider
from moltbook.client import MoltbookClient
from moltbook.models import Post
from scheduler import Scheduler
from ui.base import UserInterface


class BotEngine:
    def __init__(
        self,
        config: AppConfig,
        client: MoltbookClient,
        llm: LLMProvider,
        scheduler: Scheduler,
        ui: UserInterface,
    ) -> None:
        self.config = config
        self.client = client
        self.llm = llm
        self.scheduler = scheduler
        self.ui = ui
        self._running = False
        self._paused = False

    async def run(self) -> None:
        self._running = True
        await self.ui.start()
        await self.ui.send_status("TinyMolty started.")
        try:
            while self._running:
                await self._handle_commands()
                if self._paused:
                    await asyncio.sleep(1)
                    continue
                await self._tick()
        finally:
            await self.ui.stop()

    async def _handle_commands(self) -> None:
        command = await self.ui.get_command()
        if not command:
            return
        if command == "pause":
            self._paused = True
            await self.ui.send_status("Paused.")
        elif command == "resume":
            self._paused = False
            await self.ui.send_status("Resumed.")
        elif command == "status":
            await self.ui.send_status("Running." if not self._paused else "Paused.")
        elif command == "quit":
            self._running = False
            await self.ui.send_status("Shutting down.")

    async def _tick(self) -> None:
        await self._maybe_heartbeat()
        await self._maybe_browse()
        await self._maybe_post()
        next_wait = min(
            [
                self.scheduler.next_available_in("browse"),
                self.scheduler.next_available_in("comment"),
                self.scheduler.next_available_in("post"),
                self.scheduler.next_available_in("heartbeat"),
            ]
        )
        await self.ui.update_activity("Sleeping", next_wait)
        await self.scheduler.sleep_with_jitter(max(5.0, next_wait))

    async def _maybe_heartbeat(self) -> None:
        if not self.scheduler.can_do("heartbeat"):
            return
        await self.ui.update_activity("Sending heartbeat")
        await self.client.heartbeat()
        self.scheduler.record_action("heartbeat")

    async def _maybe_browse(self) -> None:
        if not self.scheduler.can_do("browse"):
            return
        await self.ui.update_activity("Browsing feed")
        feed = await self.client.get_feed()
        self.scheduler.record_action("browse")
        if not feed.posts:
            return
        scored = await self._score_posts(feed.posts)
        await self._maybe_interact(scored)

    async def _maybe_interact(self, posts: list[Post]) -> None:
        for post in posts:
            if self.scheduler.can_do("comment"):
                comment = await self._generate_comment(post)
                await self.ui.send_status(f"Commenting on {post.id}")
                await self.client.comment(post.id, comment)
                self.scheduler.record_action("comment")
            if self.scheduler.can_do("upvote"):
                await self.ui.send_status(f"Upvoting {post.id}")
                await self.client.upvote(post.id)
                self.scheduler.record_action("upvote")
            if self.scheduler.can_do("follow") and post.author:
                await self.ui.send_status(f"Following {post.author.id}")
                await self.client.follow(post.author.id)
                self.scheduler.record_action("follow")
            break

    async def _maybe_post(self) -> None:
        if not self.scheduler.can_do("post"):
            return
        await self.ui.update_activity("Creating post")
        content = await self._generate_post()
        await self.client.create_post(
            content=content,
            submolt=random.choice(self.config.behavior.preferred_submolts)
            if self.config.behavior.preferred_submolts
            else None,
        )
        self.scheduler.record_action("post")
        await self.ui.send_status("Posted new content.")

    async def _score_posts(self, posts: Iterable[Post]) -> list[Post]:
        prompt_lines = [
            "Score each post from 0 to 1 for interest given topics of interest.",
            f"Topics: {', '.join(self.config.personality.topics_of_interest)}",
        ]
        for post in posts:
            prompt_lines.append(f"{post.id}: {post.content[:200]}")
        prompt_lines.append("Return JSON array of {id, score}.")
        try:
            response = await self.llm.generate(self.config.personality.system_prompt, "\n".join(prompt_lines))
            data = json.loads(response.content)
            scores = {item["id"]: float(item["score"]) for item in data}
            ranked = sorted(posts, key=lambda p: scores.get(p.id, 0.0), reverse=True)
            return ranked[:5]
        except Exception:
            return list(posts)[:5]

    async def _generate_comment(self, post: Post) -> str:
        prompt = (
            "Write a short, friendly comment in one sentence.\n"
            f"Post: {post.content[:500]}"
        )
        try:
            response = await self.llm.generate(self.config.personality.system_prompt, prompt)
            return response.content.strip()[:400]
        except Exception:
            return "Interesting perspective! Thanks for sharing."

    async def _generate_post(self) -> str:
        prompt = (
            "Create an original post for Moltbook. Keep it under 500 characters.\n"
            f"Topics: {', '.join(self.config.personality.topics_of_interest)}"
        )
        try:
            response = await self.llm.generate(self.config.personality.system_prompt, prompt)
            return response.content.strip()[:500]
        except Exception:
            return "Exploring new ideas today—what concepts are you curious about?"
