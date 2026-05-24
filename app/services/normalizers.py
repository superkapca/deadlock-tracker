from datetime import UTC, datetime
from typing import Any


def first_item(payload: Any) -> Any:
    if isinstance(payload, list):
        return payload[0] if payload else None
    if isinstance(payload, dict):
        for key in ("data", "items", "results"):
            value = payload.get(key)
            if isinstance(value, list):
                return value[0] if value else None
        return payload
    return None


def extract_account_id(profile: dict[str, Any], fallback: int | None = None) -> int | None:
    for key in ("account_id", "accountId", "steam_id", "steamid", "id"):
        value = profile.get(key)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
    return fallback


def extract_display_name(profile: dict[str, Any] | None) -> str | None:
    if not profile:
        return None
    for key in ("personaname", "persona_name", "name", "display_name", "username"):
        value = profile.get(key)
        if value:
            return str(value)
    return None


def extract_avatar_url(profile: dict[str, Any] | None) -> str | None:
    if not profile:
        return None
    for key in ("avatarfull", "avatar_full", "avatar_url", "avatar", "avatar_medium"):
        value = profile.get(key)
        if value:
            return str(value)
    return None


def extract_match_id(match: dict[str, Any]) -> int | None:
    for key in ("match_id", "matchId", "id"):
        value = match.get(key)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
    return None


def extract_hero_id(match: dict[str, Any]) -> int | None:
    for key in ("hero_id", "heroId", "hero"):
        value = match.get(key)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
    return None


def extract_started_at(payload: dict[str, Any]) -> datetime | None:
    for key in ("start_time", "start_time_unix", "start_unix_timestamp", "unix_timestamp"):
        value = payload.get(key)
        if value is not None:
            try:
                return datetime.fromtimestamp(int(value), UTC)
            except (TypeError, ValueError, OSError):
                continue
    for key in ("started_at", "start_time_iso"):
        value = payload.get(key)
        if value:
            try:
                parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=UTC)
            except ValueError:
                continue
    return None


def extract_duration(payload: dict[str, Any]) -> int | None:
    for key in ("duration_s", "duration_sec", "duration"):
        value = payload.get(key)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
    return None


def extract_average_badge(payload: dict[str, Any]) -> int | None:
    for key in ("average_badge", "avg_badge", "match_average_badge"):
        value = payload.get(key)
        if value is not None:
            try:
                return int(value)
            except (TypeError, ValueError):
                continue
    return None


def extract_result(match: dict[str, Any]) -> str | None:
    for key in ("result", "match_result", "win"):
        value = match.get(key)
        if isinstance(value, bool):
            return "win" if value else "loss"
        if value is not None:
            return str(value)
    return None
