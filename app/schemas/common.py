from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict


class RawPayload(BaseModel):
    model_config = ConfigDict(extra="allow")


class PlayerProfile(BaseModel):
    account_id: int | None
    display_name: str | None = None
    avatar_url: str | None = None
    last_seen_at: datetime | None = None
    refreshed_at: datetime | None = None
    raw: dict[str, Any] | None = None


class MatchCard(BaseModel):
    account_id: int
    match_id: int
    hero_id: int | None = None
    result: str | None = None
    started_at: datetime | None = None
    summary: dict[str, Any]


class MatchDetail(BaseModel):
    match_id: int
    started_at: datetime | None = None
    duration_s: int | None = None
    average_badge: int | None = None
    summary: dict[str, Any] | list[Any] | None = None
    metadata: dict[str, Any] | list[Any] | None = None
