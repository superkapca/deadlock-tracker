from datetime import timedelta
from typing import Any

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import UpstreamError, UpstreamNotFound
from app.db.models import Match, PlayerMatchHistory
from app.services.cache import is_fresh, upsert_json, utcnow
from app.services.deadlock_client import DeadlockApiClient, get_deadlock_client
from app.services.normalizers import (
    extract_average_badge,
    extract_duration,
    extract_hero_id,
    extract_match_id,
    extract_result,
    extract_started_at,
    first_item,
)


class MatchService:
    def __init__(self, db: AsyncSession, client: DeadlockApiClient | None = None) -> None:
        self.db = db
        self.client = client or get_deadlock_client()
        self.settings = get_settings()

    async def get_player_matches(self, account_id: int, limit: int = 20) -> list[dict[str, Any]]:
        cached = await self._get_cached_history(account_id, limit)
        ttl = timedelta(minutes=self.settings.cache_player_ttl_minutes)
        if cached and is_fresh(max(item.refreshed_at for item in cached), ttl):
            return [self._history_row_to_response(row) for row in cached]

        try:
            history = await self.client.get_match_history(account_id)
        except UpstreamError:
            if cached:
                return [self._history_row_to_response(row) for row in cached]
            raise

        rows = history if isinstance(history, list) else history.get("matches", []) if isinstance(history, dict) else []
        for raw_match in rows[:limit]:
            if not isinstance(raw_match, dict):
                continue
            match_id = extract_match_id(raw_match)
            if match_id is None:
                continue
            started_at = extract_started_at(raw_match)
            await upsert_json(
                self.db,
                Match,
                {
                    "match_id": match_id,
                    "summary_json": raw_match,
                    "metadata_json": None,
                    "started_at": started_at,
                    "duration_s": extract_duration(raw_match),
                    "average_badge": extract_average_badge(raw_match),
                    "refreshed_at": utcnow(),
                },
                ["match_id"],
                ["summary_json", "started_at", "duration_s", "average_badge", "refreshed_at"],
            )
            await upsert_json(
                self.db,
                PlayerMatchHistory,
                {
                    "account_id": account_id,
                    "match_id": match_id,
                    "hero_id": extract_hero_id(raw_match),
                    "result": extract_result(raw_match),
                    "started_at": started_at,
                    "summary_json": raw_match,
                    "refreshed_at": utcnow(),
                },
                ["account_id", "match_id"],
                ["hero_id", "result", "started_at", "summary_json", "refreshed_at"],
            )

        await self.db.commit()
        refreshed = await self._get_cached_history(account_id, limit)
        return [self._history_row_to_response(row) for row in refreshed]

    async def get_match(self, match_id: int) -> dict[str, Any]:
        cached = await self._get_cached_match(match_id)
        ttl = timedelta(hours=self.settings.cache_match_ttl_hours)
        if cached and cached.metadata_json and is_fresh(cached.refreshed_at, ttl):
            return self._match_row_to_response(cached)

        try:
            payload = await self.client.get_match_metadata(match_id)
        except UpstreamError:
            if cached and (cached.metadata_json or cached.summary_json):
                return self._match_row_to_response(cached)
            raise

        metadata = first_item(payload) or payload
        if not metadata:
            raise UpstreamNotFound("Match was not found")

        await upsert_json(
            self.db,
            Match,
            {
                "match_id": match_id,
                "summary_json": cached.summary_json if cached else None,
                "metadata_json": metadata,
                "started_at": extract_started_at(metadata) if isinstance(metadata, dict) else None,
                "duration_s": extract_duration(metadata) if isinstance(metadata, dict) else None,
                "average_badge": extract_average_badge(metadata) if isinstance(metadata, dict) else None,
                "refreshed_at": utcnow(),
            },
            ["match_id"],
            ["metadata_json", "started_at", "duration_s", "average_badge", "refreshed_at"],
        )
        await self.db.commit()
        row = await self._get_cached_match(match_id)
        if row is None:
            raise UpstreamNotFound("Match was not found")
        return self._match_row_to_response(row)

    async def hydrate_matches(self, match_ids: list[int]) -> None:
        if not match_ids:
            return
        try:
            payload = await self.client.get_bulk_match_metadata(match_ids)
        except UpstreamError:
            return

        rows = payload if isinstance(payload, list) else payload.get("matches", []) if isinstance(payload, dict) else []
        for raw_match in rows:
            if not isinstance(raw_match, dict):
                continue
            match_id = extract_match_id(raw_match)
            if match_id is None:
                continue
            await upsert_json(
                self.db,
                Match,
                {
                    "match_id": match_id,
                    "summary_json": raw_match,
                    "metadata_json": raw_match,
                    "started_at": extract_started_at(raw_match),
                    "duration_s": extract_duration(raw_match),
                    "average_badge": extract_average_badge(raw_match),
                    "refreshed_at": utcnow(),
                },
                ["match_id"],
                ["metadata_json", "started_at", "duration_s", "average_badge", "refreshed_at"],
            )
        await self.db.commit()

    async def _get_cached_history(self, account_id: int, limit: int) -> list[PlayerMatchHistory]:
        result = await self.db.execute(
            select(PlayerMatchHistory)
            .where(PlayerMatchHistory.account_id == account_id)
            .order_by(desc(PlayerMatchHistory.started_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def _get_cached_match(self, match_id: int) -> Match | None:
        result = await self.db.execute(select(Match).where(Match.match_id == match_id))
        return result.scalar_one_or_none()

    def _history_row_to_response(self, row: PlayerMatchHistory) -> dict[str, Any]:
        return {
            "account_id": row.account_id,
            "match_id": row.match_id,
            "hero_id": row.hero_id,
            "result": row.result,
            "started_at": row.started_at,
            "summary": row.summary_json,
        }

    def _match_row_to_response(self, row: Match) -> dict[str, Any]:
        return {
            "match_id": row.match_id,
            "started_at": row.started_at,
            "duration_s": row.duration_s,
            "average_badge": row.average_badge,
            "summary": row.summary_json,
            "metadata": row.metadata_json,
        }
