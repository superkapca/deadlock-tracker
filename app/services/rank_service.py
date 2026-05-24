from datetime import timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import UpstreamError
from app.db.models import PlayerMmrHistory, PlayerRankCache
from app.services.cache import is_fresh, upsert_json, utcnow
from app.services.deadlock_client import DeadlockApiClient, get_deadlock_client


class RankService:
    def __init__(self, db: AsyncSession, client: DeadlockApiClient | None = None) -> None:
        self.db = db
        self.client = client or get_deadlock_client()
        self.settings = get_settings()

    async def get_rank(self, account_id: int) -> dict[str, Any]:
        cached = await self._get_rank_cache(account_id)
        ttl = timedelta(minutes=self.settings.cache_mmr_ttl_minutes)
        if cached and is_fresh(cached.refreshed_at, ttl):
            return {"account_id": account_id, "mmr": cached.mmr_json, "rank_predict": cached.rank_predict_json}

        try:
            mmr = await self.client.get_mmr(account_id)
            rank_predict = await self.client.get_rank_predict(account_id)
        except UpstreamError:
            if cached:
                return {"account_id": account_id, "mmr": cached.mmr_json, "rank_predict": cached.rank_predict_json}
            raise

        await upsert_json(
            self.db,
            PlayerRankCache,
            {
                "account_id": account_id,
                "mmr_json": mmr,
                "rank_predict_json": rank_predict,
                "refreshed_at": utcnow(),
            },
            ["account_id"],
            ["mmr_json", "rank_predict_json", "refreshed_at"],
        )
        await self.db.commit()
        return {"account_id": account_id, "mmr": mmr, "rank_predict": rank_predict}

    async def get_mmr_history(self, account_id: int) -> dict[str, Any]:
        cached = await self._get_history_cache(account_id)
        ttl = timedelta(minutes=self.settings.cache_mmr_ttl_minutes)
        if cached and is_fresh(cached.refreshed_at, ttl):
            return {"account_id": account_id, "history": cached.history_json}

        try:
            history = await self.client.get_mmr_history(account_id)
        except UpstreamError:
            if cached:
                return {"account_id": account_id, "history": cached.history_json}
            raise

        await upsert_json(
            self.db,
            PlayerMmrHistory,
            {"account_id": account_id, "history_json": history, "refreshed_at": utcnow()},
            ["account_id"],
            ["history_json", "refreshed_at"],
        )
        await self.db.commit()
        return {"account_id": account_id, "history": history}

    async def _get_rank_cache(self, account_id: int) -> PlayerRankCache | None:
        result = await self.db.execute(select(PlayerRankCache).where(PlayerRankCache.account_id == account_id))
        return result.scalar_one_or_none()

    async def _get_history_cache(self, account_id: int) -> PlayerMmrHistory | None:
        result = await self.db.execute(select(PlayerMmrHistory).where(PlayerMmrHistory.account_id == account_id))
        return result.scalar_one_or_none()
