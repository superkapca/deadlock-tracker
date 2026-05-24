import pytest
import respx
from httpx import Response

from app.core.errors import UpstreamRateLimited
from app.services.deadlock_client import DeadlockApiClient


@pytest.mark.asyncio
@respx.mock
async def test_deadlock_client_searches_profiles() -> None:
    route = respx.get("https://api.deadlock-api.com/v1/players/steam-search").mock(
        return_value=Response(200, json=[{"account_id": 1, "personaname": "Seven"}])
    )
    client = DeadlockApiClient()

    payload = await client.search_steam_profiles("Seven")

    await client.close()
    assert route.called
    assert payload[0]["account_id"] == 1


@pytest.mark.asyncio
@respx.mock
async def test_deadlock_client_maps_rate_limits() -> None:
    respx.get("https://api.deadlock-api.com/v1/players/mmr").mock(return_value=Response(429))
    client = DeadlockApiClient()

    with pytest.raises(UpstreamRateLimited):
        await client.get_mmr(1)

    await client.close()
