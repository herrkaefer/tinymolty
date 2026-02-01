from __future__ import annotations

import asyncio
import json
import random
from typing import Iterable

import httpx
from email.utils import parsedate_to_datetime

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
        self._post_failures = 0

    async def run(self) -> None:
        self._running = True
        await self.ui.start()
        await self.ui.send_status("🦀 TinyMolty started.")

        # Check account status
        try:
            response = await self.client.get_me()
            # API returns {"success": true, "agent": {...}}
            agent_data = response.get("agent", {})

            agent_name = agent_data.get("name", "Unknown")
            is_claimed = agent_data.get("is_claimed", False)
            karma = agent_data.get("karma", 0)
            stats = agent_data.get("stats", {})

            await self.ui.send_status(f"👤 Logged in as: {agent_name}")
            await self.ui.send_status(f"   Karma: {karma} | Posts: {stats.get('posts', 0)} | Comments: {stats.get('comments', 0)}")

            if is_claimed:
                claimed_at = agent_data.get("claimed_at", "")
                owner = agent_data.get("owner", {})
                owner_name = owner.get("xName") or owner.get("xHandle", "")
                if owner_name:
                    await self.ui.send_status(f"✅ Account claimed by: {owner_name}")
                else:
                    await self.ui.send_status(f"✅ Account claimed")
            else:
                await self.ui.send_status("⚠️  Account NOT claimed - please complete claim process!")
                await self.ui.send_status("   Some actions (like posting) may fail until claimed.")
        except Exception as e:
            error_msg = str(e)
            # Show detailed error but don't stop - browsing may still work
            if "404" in error_msg:
                await self.ui.send_status(f"⚠️  Account status check unavailable (404 - endpoint may not exist)")
            elif "401" in error_msg or "403" in error_msg:
                await self.ui.send_status(f"⚠️  Account status check failed: {error_msg[:100]}")
                await self.ui.send_status(f"   Browsing may work, but posting/commenting might fail")
            else:
                await self.ui.send_status(f"⚠️  Could not verify account: {type(e).__name__}: {error_msg[:80]}")
            await self.ui.send_status(f"   Continuing anyway - browse should work with valid API key")

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
            await self.ui.send_status("⏸️  Paused.")
        elif command == "resume":
            self._paused = False
            await self.ui.send_status("▶️  Resumed.")
        elif command == "status":
            await self.ui.send_status("🦀 Running." if not self._paused else "⏸️  Paused.")
        elif command == "quit":
            self._running = False
            await self.ui.send_status("👋 Shutting down.")

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
        if next_wait <= 0:
            return
        await self._sleep_interruptible(next_wait)

    async def _sleep_interruptible(self, base_seconds: float) -> None:
        remaining = base_seconds + self.scheduler.jitter()
        while remaining > 0 and self._running:
            await self._handle_commands()
            if self._paused:
                break
            step = min(0.5, remaining)
            await asyncio.sleep(step)
            remaining -= step

    async def _maybe_heartbeat(self) -> None:
        if not self.scheduler.can_do("heartbeat"):
            return
        try:
            await self.ui.update_activity("🦀 Sending heartbeat")
            await self.client.heartbeat()
            self.scheduler.record_action("heartbeat")
            await self.ui.send_status("💓 Heartbeat sent successfully")
        except Exception as e:
            await self.ui.send_status(f"❌ Heartbeat failed: {type(e).__name__}: {str(e)}")

    async def _maybe_browse(self) -> None:
        if not self.scheduler.can_do("browse"):
            return
        try:
            await self.ui.update_activity("🦀 Browsing feed")
            feed = await self.client.get_feed()
            self.scheduler.record_action("browse")

            # Show feed stats
            post_count = len(feed.posts)
            if not feed.posts:
                await self.ui.send_status(f"📭 Feed is empty (0 posts)")
                return

            await self.ui.send_status(f"📬 Fetched {post_count} posts from feed")

            # Score and filter posts
            await self.ui.update_activity(f"🦀 Scoring {post_count} posts")
            scored = await self._score_posts(feed.posts)

            if scored:
                await self.ui.send_status(f"🎯 Found {len(scored)} interesting posts")
                await self._maybe_interact(scored)
            else:
                await self.ui.send_status(f"😴 No interesting posts found")
        except Exception as e:
            await self.ui.send_status(f"❌ Browse failed: {type(e).__name__}: {str(e)}")

    async def _maybe_interact(self, posts: list[Post]) -> None:
        interacted = False
        for post in posts:
            post_url = f"https://www.moltbook.com/posts/{post.id}"
            post_preview = post.content[:50] + "..." if len(post.content) > 50 else post.content

            if self.scheduler.can_do("comment"):
                try:
                    await self.ui.update_activity(f"🦀 Generating comment for post")
                    comment = await self._generate_comment(post)
                    await self.client.comment(post.id, comment)
                    self.scheduler.record_action("comment")
                    await self.ui.send_status(f"💬 Commented: \"{post_preview}\" - {post_url}")
                    interacted = True
                except Exception as e:
                    error_msg = str(e)
                    if "403" in error_msg or "Forbidden" in error_msg:
                        await self.ui.send_status(f"❌ Comment failed: 403 Forbidden - Account not verified")
                    else:
                        await self.ui.send_status(f"❌ Comment failed: {type(e).__name__}: {error_msg}")

            if self.scheduler.can_do("upvote"):
                try:
                    await self.client.upvote(post.id)
                    self.scheduler.record_action("upvote")
                    await self.ui.send_status(f"👍 Upvoted: \"{post_preview}\" - {post_url}")
                    interacted = True
                except Exception as e:
                    await self.ui.send_status(f"❌ Upvote failed: {type(e).__name__}: {str(e)}")

            if self.scheduler.can_do("follow") and post.author:
                try:
                    agent_url = f"https://www.moltbook.com/agents/{post.author.id}"
                    await self.client.follow(post.author.id)
                    self.scheduler.record_action("follow")
                    await self.ui.send_status(f"➕ Following {post.author.username}: {agent_url}")
                    interacted = True
                except Exception as e:
                    await self.ui.send_status(f"❌ Follow failed: {type(e).__name__}: {str(e)}")

            if interacted:
                break

        if not interacted:
            await self.ui.send_status(f"⏭️  Skipped interactions (cooldowns active)")

    async def _maybe_post(self) -> None:
        if not self.scheduler.can_do("post"):
            return
        try:
            await self.ui.update_activity("🦀 Generating post content")
            content = await self._generate_post()

            await self.ui.update_activity("🦀 Publishing post")
            response = await self.client.create_post(
                content=content,
                submolt=random.choice(self.config.behavior.preferred_submolts)
                if self.config.behavior.preferred_submolts
                else None,
            )
            self.scheduler.record_action("post")

            post_url = f"https://www.moltbook.com/posts/{response.id}"
            content_preview = content[:60] + "..." if len(content) > 60 else content
            await self.ui.send_status(f"📝 Posted: \"{content_preview}\" - {post_url}")
            self._post_failures = 0
        except httpx.ReadTimeout:
            await self._handle_post_failure("ReadTimeout")
        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            if status == 429:
                retry_after = self._parse_retry_after(e.response.headers)
                backoff = retry_after or self.config.behavior.post_cooldown_minutes * 60
                self.scheduler.record_backoff("post", backoff)
                await self.ui.send_status(
                    f"❌ Post failed: 429 Too Many Requests - backing off for {backoff}s"
                )
            elif status == 403:
                await self.ui.send_status("❌ Post failed: 403 Forbidden - Account may not be verified")
                await self.ui.send_status("   Check your claim URL and complete human verification")
                await self._handle_post_failure("403 Forbidden")
            else:
                await self.ui.send_status(f"❌ Post failed: HTTP {status} - {e.response.text[:200]}")
                await self._handle_post_failure(f"HTTP {status}")
        except Exception as e:
            error_msg = str(e)
            await self.ui.send_status(f"❌ Post failed: {type(e).__name__}: {error_msg}")
            await self._handle_post_failure(type(e).__name__)

    async def _score_posts(self, posts: Iterable[Post]) -> list[Post]:
        prompt_lines = [
            "Score each post from 0 to 1 for interest given topics of interest.",
            f"Topics: {', '.join(self.config.personality.topics_of_interest)}",
            "",
            "Posts to score:"
        ]
        for post in posts:
            prompt_lines.append(f"{post.id}: {post.content[:200]}")
        prompt_lines.extend([
            "",
            "IMPORTANT: Return ONLY a valid JSON array, nothing else. Format:",
            '[{"id": "post_id", "score": 0.8}, {"id": "post_id2", "score": 0.5}]'
        ])
        try:
            response = await self.llm.generate(
                "You are a helpful assistant that returns valid JSON.",
                "\n".join(prompt_lines)
            )
            # Try to extract JSON from response (handle markdown code blocks)
            content = response.content.strip()
            if content.startswith("```"):
                # Remove markdown code block markers
                lines = content.split("\n")
                content = "\n".join(line for line in lines if not line.startswith("```"))
            content = content.strip()

            data = json.loads(content)
            scores = {item["id"]: float(item["score"]) for item in data}
            ranked = sorted(posts, key=lambda p: scores.get(p.id, 0.0), reverse=True)
            return ranked[:5]
        except json.JSONDecodeError as e:
            await self.ui.send_status(f"⚠️  LLM returned invalid JSON, using first 5 posts")
            # Log the actual response for debugging
            await self.ui.send_status(f"   (Response was: {response.content[:100]}...)")
            return list(posts)[:5]
        except Exception as e:
            await self.ui.send_status(f"⚠️  LLM scoring failed ({type(e).__name__}), using first 5 posts")
            return list(posts)[:5]

    async def _generate_comment(self, post: Post) -> str:
        prompt = (
            "Write a short, friendly comment in one sentence.\n"
            f"Post: {post.content[:500]}"
        )
        try:
            response = await self.llm.generate(self.config.personality.system_prompt, prompt)
            return response.content.strip()[:400]
        except Exception as e:
            await self.ui.send_status(f"⚠️  LLM comment generation failed ({type(e).__name__}), using fallback")
            return "Interesting perspective! Thanks for sharing."

    def _parse_retry_after(self, headers: httpx.Headers) -> int | None:
        # Prefer standard Retry-After (seconds or HTTP date), then X-RateLimit-Reset (epoch seconds)
        retry_after = headers.get("Retry-After") or headers.get("retry-after")
        if retry_after:
            try:
                return max(0, int(float(retry_after)))
            except ValueError:
                try:
                    dt = parsedate_to_datetime(retry_after)
                    seconds = int((dt - datetime.utcnow()).total_seconds())
                    return max(0, seconds)
                except Exception:
                    pass
        reset = headers.get("X-RateLimit-Reset") or headers.get("x-ratelimit-reset")
        if reset:
            try:
                reset_ts = int(float(reset))
                seconds = int(reset_ts - datetime.utcnow().timestamp())
                return max(0, seconds)
            except ValueError:
                return None
        return None

    async def _handle_post_failure(self, reason: str) -> None:
        self._post_failures += 1
        if self._post_failures >= 3:
            self._post_failures = 0
            backoff = self.config.behavior.post_cooldown_minutes * 60
            self.scheduler.record_backoff("post", backoff)
            await self.ui.send_status(
                f"⏳ Post paused after 3 failures ({reason}); cooldown {backoff}s"
            )
        else:
            self.scheduler.record_backoff("post", 30)
            await self.ui.send_status(
                f"⏱️  Post retry in 30s ({self._post_failures}/3) - {reason}"
            )

    async def _generate_post(self) -> str:
        posts_summary: list[str] = []
        try:
            hot_feed = await self.client.get_posts(sort="hot", limit=8)
            for post in hot_feed.posts:
                content = post.content.strip().replace("\n", " ")
                if not content:
                    continue
                posts_summary.append(f"- {content[:160]}")
        except Exception:
            posts_summary = []

        prompt = (
            "Create an original post for Moltbook. Keep it under 500 characters.\n"
            f"Topics: {', '.join(self.config.personality.topics_of_interest)}"
        )
        if posts_summary:
            prompt += "\n\nRecent hot posts for context (do not quote verbatim):\n" + "\n".join(posts_summary)
        try:
            response = await self.llm.generate(self.config.personality.system_prompt, prompt)
            return response.content.strip()[:500]
        except Exception as e:
            await self.ui.send_status(f"⚠️  LLM post generation failed ({type(e).__name__}), using fallback")
            return "Exploring new ideas today—what concepts are you curious about?"
