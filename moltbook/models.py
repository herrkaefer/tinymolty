from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, field_validator


class AgentProfile(BaseModel):
    id: str | None = None
    username: str | None = None
    display_name: str | None = None


class Post(BaseModel):
    id: str
    author: AgentProfile | None = None
    title: str = ""
    content: str = ""
    created_at: datetime | None = None
    submolt: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)

    @field_validator("title", "content", mode="before")
    @classmethod
    def _validate_text_fields(cls, value: Any) -> str:
        """Convert None to empty string for text fields"""
        if value is None:
            return ""
        return str(value)

    @field_validator("submolt", mode="before")
    @classmethod
    def _validate_submolt(cls, value: Any) -> str | None:
        """Convert submolt to string or None, handling any input type"""
        if value is None or value == "":
            return None
        # Convert to string if it's not already
        if isinstance(value, str):
            return value
        # For other types (int, list, dict, etc.), convert to string
        return str(value)


class FeedResponse(BaseModel):
    posts: list[Post] = Field(default_factory=list)


class CreatePostResponse(BaseModel):
    id: str | None = None
    success: bool | None = None
    message: str | None = None
