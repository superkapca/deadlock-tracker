from typing import Any

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import MatchCard, PlayerProfile
from app.services.match_service import MatchService
from app.services.player_service import PlayerService
from app.services.rank_service import RankService


router = APIRouter()


@router.get("/search", response_model=list[PlayerProfile])
async def search_players(
    q: str = Query(..., min_length=2),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    return await PlayerService(db).search(q, limit)


@router.get("/{account_id}", response_model=PlayerProfile)
async def player_profile(
    account_id: int = Path(..., ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await PlayerService(db).get_profile(account_id)


@router.get("/{account_id}/summary")
async def player_summary(
    account_id: int = Path(..., ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await PlayerService(db).get_summary(account_id)


@router.get("/{account_id}/matches", response_model=list[MatchCard])
async def player_matches(
    account_id: int = Path(..., ge=0),
    limit: int = Query(20, ge=1, le=100),
    hydrate: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> list[dict[str, Any]]:
    service = MatchService(db)
    matches = await service.get_player_matches(account_id, limit)
    if hydrate:
        await service.hydrate_matches([item["match_id"] for item in matches])
    return matches


@router.get("/{account_id}/hero-stats")
async def player_hero_stats(
    account_id: int = Path(..., ge=0),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await PlayerService(db).get_hero_stats(account_id)


@router.get("/{account_id}/rank")
async def player_rank(
    account_id: int = Path(..., ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await RankService(db).get_rank(account_id)


@router.get("/{account_id}/mmr-history")
async def player_mmr_history(
    account_id: int = Path(..., ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    return await RankService(db).get_mmr_history(account_id)
