from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class AgentProfile(BaseModel):
    id: str
    username: str
    display_name: str | None = None


class Post(BaseModel):
    id: str
    author: AgentProfile | None = None
    content: str = ""
    created_at: datetime | None = None
    submolt: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


class FeedResponse(BaseModel):
    posts: list[Post] = Field(default_factory=list)


class CreatePostResponse(BaseModel):
    id: str
