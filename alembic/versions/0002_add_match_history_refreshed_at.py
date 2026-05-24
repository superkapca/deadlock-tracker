"""add match history refreshed at

Revision ID: 0002_match_refreshed
Revises: 0001_initial_cache_schema
Create Date: 2026-05-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0002_match_refreshed"
down_revision: Union[str, None] = "0001_initial_cache_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "player_match_history",
        sa.Column("refreshed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade() -> None:
    op.drop_column("player_match_history", "refreshed_at")
