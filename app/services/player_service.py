from datetime import timedelta
from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import UpstreamError, UpstreamNotFound
from app.db.models import Player, PlayerAccountStats, PlayerHeroStats
from app.services.cache import is_fresh, upsert_json, utcnow
from app.services.deadlock_client import DeadlockApiClient, get_deadlock_client
from app.services.match_service import MatchService
from app.services.normalizers import extract_account_id, extract_avatar_url, extract_display_name, first_item
from app.services.rank_service import RankService


class PlayerService:
    def __init__(self, db: AsyncSession, client: DeadlockApiClient | None = None) -> None:
        self.db = db
        self.client = client or get_deadlock_client()
        self.settings = get_settings()

    async def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        payload = await self.client.search_steam_profiles(query, limit)
        rows = payload if isinstance(payload, list) else payload.get("results", []) if isinstance(payload, dict) else []
        return [self._profile_to_response(item) for item in rows if isinstance(item, dict)]

    async def get_profile(self, account_id: int) -> dict[str, Any]:
        cached = await self._get_cached_player(account_id)
        ttl = timedelta(minutes=self.settings.cache_player_ttl_minutes)
        if cached and is_fresh(cached.refreshed_at, ttl):
            return self._player_row_to_response(cached)

        try:
            payload = await self.client.get_steam_profiles([account_id])
        except UpstreamError:
            if cached:
                return self._player_row_to_response(cached)
            raise

        profile = first_item(payload)
        if not isinstance(profile, dict):
            if cached:
                return self._player_row_to_response(cached)
            raise UpstreamNotFound("Player was not found")

        await self._save_profile(account_id, profile)
        await self.db.commit()
        row = await self._get_cached_player(account_id)
        if row is None:
            raise UpstreamNotFound("Player was not found")
        return self._player_row_to_response(row)

    async def get_account_stats(self, account_id: int) -> Any:
        cached = await self._get_account_stats(account_id)
        ttl = timedelta(minutes=self.settings.cache_player_ttl_minutes)
        if cached and is_fresh(cached.refreshed_at, ttl):
            return cached.stats_json

        try:
            payload = await self.client.get_account_stats(account_id)
        except UpstreamError:
            if cached:
                return cached.stats_json
            raise

        await upsert_json(
            self.db,
            PlayerAccountStats,
            {"account_id": account_id, "stats_json": payload, "refreshed_at": utcnow()},
            ["account_id"],
            ["stats_json", "refreshed_at"],
        )
        await self.db.commit()
        return payload

    async def get_hero_stats(self, account_id: int) -> list[dict[str, Any]]:
        cached = await self._get_hero_stats(account_id)
        ttl = timedelta(minutes=self.settings.cache_player_ttl_minutes)
        if cached and is_fresh(max(row.refreshed_at for row in cached), ttl):
            return [row.stats_json for row in cached]

        try:
            payload = await self.client.get_hero_stats(account_id)
        except UpstreamError:
            if cached:
                return [row.stats_json for row in cached]
            raise

        rows = payload if isinstance(payload, list) else payload.get("hero_stats", []) if isinstance(payload, dict) else []
        await self.db.execute(delete(PlayerHeroStats).where(PlayerHeroStats.account_id == account_id))
        for item in rows:
            if not isinstance(item, dict):
                continue
            hero_id = item.get("hero_id") or item.get("heroId") or item.get("hero")
            try:
                hero_id_int = int(hero_id)
            except (TypeError, ValueError):
                continue
            self.db.add(
                PlayerHeroStats(
                    account_id=account_id,
                    hero_id=hero_id_int,
                    stats_json=item,
                    refreshed_at=utcnow(),
                )
            )
        await self.db.commit()
        refreshed = await self._get_hero_stats(account_id)
        return [row.stats_json for row in refreshed]

    async def get_summary(self, account_id: int) -> dict[str, Any]:
        profile = await self.get_profile(account_id)
        errors: list[dict[str, str]] = []

        account_stats = await self._optional_summary_part("account_stats", errors, self.get_account_stats(account_id))
        hero_stats = await self._optional_summary_part("hero_stats", errors, self.get_hero_stats(account_id))
        matches = await self._optional_summary_part(
            "recent_matches",
            errors,
            MatchService(self.db, self.client).get_player_matches(account_id, limit=10),
        )
        rank = await self._optional_summary_part("rank", errors, RankService(self.db, self.client).get_rank(account_id))
        return {
            "profile": profile,
            "account_stats": account_stats,
            "hero_stats": hero_stats,
            "recent_matches": matches,
            "rank": rank,
            "errors": errors,
        }

    async def _optional_summary_part(self, name: str, errors: list[dict[str, str]], awaitable: Any) -> Any:
        try:
            return await awaitable
        except UpstreamError as exc:
            errors.append({"section": name, "detail": exc.message})
            return None

    async def _save_profile(self, account_id: int, profile: dict[str, Any]) -> None:
        await upsert_json(
            self.db,
            Player,
            {
                "account_id": extract_account_id(profile, account_id) or account_id,
                "steam_profile_json": profile,
                "display_name": extract_display_name(profile),
                "avatar_url": extract_avatar_url(profile),
                "last_seen_at": utcnow(),
                "refreshed_at": utcnow(),
            },
            ["account_id"],
            ["steam_profile_json", "display_name", "avatar_url", "last_seen_at", "refreshed_at"],
        )

    async def _get_cached_player(self, account_id: int) -> Player | None:
        result = await self.db.execute(select(Player).where(Player.account_id == account_id))
        return result.scalar_one_or_none()

    async def _get_account_stats(self, account_id: int) -> PlayerAccountStats | None:
        result = await self.db.execute(select(PlayerAccountStats).where(PlayerAccountStats.account_id == account_id))
        return result.scalar_one_or_none()

    async def _get_hero_stats(self, account_id: int) -> list[PlayerHeroStats]:
        result = await self.db.execute(select(PlayerHeroStats).where(PlayerHeroStats.account_id == account_id))
        return list(result.scalars().all())

    def _profile_to_response(self, profile: dict[str, Any]) -> dict[str, Any]:
        return {
            "account_id": extract_account_id(profile),
            "display_name": extract_display_name(profile),
            "avatar_url": extract_avatar_url(profile),
            "raw": profile,
        }

    def _player_row_to_response(self, row: Player) -> dict[str, Any]:
        return {
            "account_id": row.account_id,
            "display_name": row.display_name,
            "avatar_url": row.avatar_url,
            "last_seen_at": row.last_seen_at,
            "refreshed_at": row.refreshed_at,
            "raw": row.steam_profile_json,
        }
