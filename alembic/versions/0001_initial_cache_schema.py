"""initial cache schema

Revision ID: 0001_initial_cache_schema
Revises:
Create Date: 2026-05-24
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial_cache_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "players",
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("steam_profile_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("display_name", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.Text(), nullable=True),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("refreshed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("account_id"),
    )
    op.create_table(
        "player_account_stats",
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("stats_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("refreshed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("account_id"),
    )
    op.create_table(
        "player_hero_stats",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("hero_id", sa.Integer(), nullable=False),
        sa.Column("stats_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("refreshed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_player_hero_stats_account_hero", "player_hero_stats", ["account_id", "hero_id"], unique=True)
    op.create_table(
        "player_rank_cache",
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("mmr_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("rank_predict_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("refreshed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("account_id"),
    )
    op.create_table(
        "player_mmr_history",
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("history_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("refreshed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("account_id"),
    )
    op.create_table(
        "matches",
        sa.Column("match_id", sa.BigInteger(), nullable=False),
        sa.Column("summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("metadata_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("duration_s", sa.Integer(), nullable=True),
        sa.Column("average_badge", sa.Integer(), nullable=True),
        sa.Column("refreshed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("match_id"),
    )
    op.create_index("ix_matches_started_at", "matches", ["started_at"], unique=False)
    op.create_table(
        "player_match_history",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("match_id", sa.BigInteger(), nullable=False),
        sa.Column("hero_id", sa.Integer(), nullable=True),
        sa.Column("result", sa.String(length=32), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_player_match_history_account_started", "player_match_history", ["account_id", "started_at"])
    op.create_index("ix_player_match_history_match", "player_match_history", ["match_id"])
    op.create_index("ux_player_match_history_account_match", "player_match_history", ["account_id", "match_id"], unique=True)
    op.create_table(
        "static_assets",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("asset_type", sa.String(length=64), nullable=False),
        sa.Column("asset_key", sa.String(length=128), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("refreshed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ux_static_assets_type_key", "static_assets", ["asset_type", "asset_key"], unique=True)


def downgrade() -> None:
    op.drop_index("ux_static_assets_type_key", table_name="static_assets")
    op.drop_table("static_assets")
    op.drop_index("ux_player_match_history_account_match", table_name="player_match_history")
    op.drop_index("ix_player_match_history_match", table_name="player_match_history")
    op.drop_index("ix_player_match_history_account_started", table_name="player_match_history")
    op.drop_table("player_match_history")
    op.drop_index("ix_matches_started_at", table_name="matches")
    op.drop_table("matches")
    op.drop_table("player_mmr_history")
    op.drop_table("player_rank_cache")
    op.drop_index("ix_player_hero_stats_account_hero", table_name="player_hero_stats")
    op.drop_table("player_hero_stats")
    op.drop_table("player_account_stats")
    op.drop_table("players")
