from typing import Any

import httpx

from app.core.config import get_settings
from app.core.errors import UpstreamError, UpstreamNotFound, UpstreamRateLimited, UpstreamTimeout


class DeadlockApiClient:
    def __init__(self) -> None:
        settings = get_settings()
        headers = {"X-API-KEY": settings.deadlock_api_key} if settings.deadlock_api_key else {}
        self._client = httpx.AsyncClient(
            base_url=settings.deadlock_api_base_url.rstrip("/"),
            headers=headers,
            timeout=settings.http_timeout_seconds,
        )

    async def close(self) -> None:
        await self._client.aclose()

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> Any:
        try:
            response = await self._client.get(path, params=params)
        except httpx.TimeoutException as exc:
            raise UpstreamTimeout("Deadlock API timed out") from exc
        except httpx.HTTPError as exc:
            raise UpstreamError("Could not reach Deadlock API") from exc

        if response.status_code == 404:
            raise UpstreamNotFound("Deadlock API resource was not found")
        if response.status_code == 429:
            raise UpstreamRateLimited("Deadlock API rate limit reached")
        if response.status_code >= 500:
            raise UpstreamError("Deadlock API server error")
        if response.status_code >= 400:
            raise UpstreamError(f"Deadlock API rejected the request with {response.status_code}")
        return response.json()

    async def search_steam_profiles(self, query: str, limit: int = 10) -> Any:
        return await self._get("/v1/players/steam-search", {"search_query": query, "limit": limit})

    async def get_steam_profiles(self, account_ids: list[int], refresh: bool = False) -> Any:
        return await self._get("/v1/players/steam", {"account_ids": account_ids, "refresh": refresh})

    async def get_match_history(self, account_id: int) -> Any:
        return await self._get(f"/v1/players/{account_id}/match-history")

    async def get_bulk_match_metadata(self, match_ids: list[int]) -> Any:
        return await self._get(
            "/v1/matches/metadata",
            {
                "match_ids": match_ids,
                "include_player_info": True,
                "include_player_kda": True,
                "include_player_items": True,
                "include_player_stats": True,
                "include_player_final_stats": True,
                "include_objectives": True,
            },
        )

    async def get_match_metadata(self, match_id: int) -> Any:
        return await self._get(f"/v1/matches/{match_id}/metadata")

    async def get_account_stats(self, account_id: int) -> Any:
        return await self._get(f"/v1/players/{account_id}/account-stats")

    async def get_hero_stats(self, account_id: int) -> Any:
        return await self._get("/v1/players/hero-stats", {"account_ids": [account_id]})

    async def get_mmr(self, account_id: int) -> Any:
        return await self._get("/v1/players/mmr", {"account_ids": [account_id]})

    async def get_mmr_history(self, account_id: int) -> Any:
        return await self._get(f"/v1/players/{account_id}/mmr-history")

    async def get_rank_predict(self, account_id: int) -> Any:
        return await self._get(f"/v1/players/{account_id}/rank-predict")

    async def get_asset(self, asset_type: str) -> Any:
        return await self._get(f"/v1/assets/{asset_type}")


_client: DeadlockApiClient | None = None


def get_deadlock_client() -> DeadlockApiClient:
    global _client
    if _client is None:
        _client = DeadlockApiClient()
    return _client


async def close_deadlock_client() -> None:
    global _client
    if _client is not None:
        await _client.close()
        _client = None
