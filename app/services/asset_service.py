from datetime import timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import UpstreamError
from app.db.models import StaticAsset
from app.services.cache import is_fresh, upsert_json, utcnow
from app.services.deadlock_client import DeadlockApiClient, get_deadlock_client


class AssetService:
    def __init__(self, db: AsyncSession, client: DeadlockApiClient | None = None) -> None:
        self.db = db
        self.client = client or get_deadlock_client()
        self.settings = get_settings()

    async def get_assets(self, asset_type: str) -> Any:
        cached = await self._get_cached(asset_type)
        ttl = timedelta(hours=self.settings.cache_static_ttl_hours)
        if cached and is_fresh(cached.refreshed_at, ttl):
            return cached.payload_json

        try:
            payload = await self.client.get_asset(asset_type)
        except UpstreamError:
            if cached:
                return cached.payload_json
            raise

        await upsert_json(
            self.db,
            StaticAsset,
            {
                "asset_type": asset_type,
                "asset_key": "all",
                "payload_json": payload,
                "refreshed_at": utcnow(),
            },
            ["asset_type", "asset_key"],
            ["payload_json", "refreshed_at"],
        )
        await self.db.commit()
        return payload

    async def _get_cached(self, asset_type: str) -> StaticAsset | None:
        result = await self.db.execute(
            select(StaticAsset).where(StaticAsset.asset_type == asset_type, StaticAsset.asset_key == "all")
        )
        return result.scalar_one_or_none()
