from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.asset_service import AssetService


router = APIRouter()


@router.get("/heroes")
async def heroes(db: AsyncSession = Depends(get_db)) -> Any:
    return await AssetService(db).get_assets("heroes")


@router.get("/items")
async def items(db: AsyncSession = Depends(get_db)) -> Any:
    return await AssetService(db).get_assets("items")


@router.get("/ranks")
async def ranks(db: AsyncSession = Depends(get_db)) -> Any:
    return await AssetService(db).get_assets("ranks")
