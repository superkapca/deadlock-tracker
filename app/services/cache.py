from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession


def utcnow() -> datetime:
    return datetime.now(UTC)


def is_fresh(refreshed_at: datetime | None, ttl: timedelta) -> bool:
    if refreshed_at is None:
        return False
    if refreshed_at.tzinfo is None:
        refreshed_at = refreshed_at.replace(tzinfo=UTC)
    return refreshed_at + ttl > utcnow()


async def upsert_json(
    db: AsyncSession,
    model: type,
    values: dict[str, Any],
    conflict_columns: list[str],
    update_columns: list[str],
) -> None:
    stmt = insert(model).values(**values)
    stmt = stmt.on_conflict_do_update(
        index_elements=conflict_columns,
        set_={column: getattr(stmt.excluded, column) for column in update_columns},
    )
    await db.execute(stmt)
