from fastapi import APIRouter, Depends, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.common import MatchDetail
from app.services.match_service import MatchService


router = APIRouter()


@router.get("/{match_id}", response_model=MatchDetail)
async def match_detail(
    match_id: int = Path(..., ge=0),
    db: AsyncSession = Depends(get_db),
) -> dict:
    return await MatchService(db).get_match(match_id)
