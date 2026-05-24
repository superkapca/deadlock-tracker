from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Player(Base):
    __tablename__ = "players"

    account_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    steam_profile_json: Mapped[dict | None] = mapped_column(JSONB)
    display_name: Mapped[str | None] = mapped_column(Text)
    avatar_url: Mapped[str | None] = mapped_column(Text)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PlayerAccountStats(Base):
    __tablename__ = "player_account_stats"

    account_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    stats_json: Mapped[dict | list] = mapped_column(JSONB, nullable=False)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PlayerHeroStats(Base):
    __tablename__ = "player_hero_stats"
    __table_args__ = (Index("ix_player_hero_stats_account_hero", "account_id", "hero_id", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    hero_id: Mapped[int] = mapped_column(Integer, nullable=False)
    stats_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PlayerRankCache(Base):
    __tablename__ = "player_rank_cache"

    account_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    mmr_json: Mapped[dict | list | None] = mapped_column(JSONB)
    rank_predict_json: Mapped[dict | list | None] = mapped_column(JSONB)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PlayerMmrHistory(Base):
    __tablename__ = "player_mmr_history"

    account_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    history_json: Mapped[dict | list] = mapped_column(JSONB, nullable=False)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (Index("ix_matches_started_at", "started_at"),)

    match_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    summary_json: Mapped[dict | list | None] = mapped_column(JSONB)
    metadata_json: Mapped[dict | list | None] = mapped_column(JSONB)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    duration_s: Mapped[int | None] = mapped_column(Integer)
    average_badge: Mapped[int | None] = mapped_column(Integer)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class PlayerMatchHistory(Base):
    __tablename__ = "player_match_history"
    __table_args__ = (
        Index("ix_player_match_history_account_started", "account_id", "started_at"),
        Index("ix_player_match_history_match", "match_id"),
        Index("ux_player_match_history_account_match", "account_id", "match_id", unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    match_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    hero_id: Mapped[int | None] = mapped_column(Integer)
    result: Mapped[str | None] = mapped_column(String(32))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    summary_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class StaticAsset(Base):
    __tablename__ = "static_assets"
    __table_args__ = (Index("ux_static_assets_type_key", "asset_type", "asset_key", unique=True),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    asset_type: Mapped[str] = mapped_column(String(64), nullable=False)
    asset_key: Mapped[str] = mapped_column(String(128), nullable=False)
    payload_json: Mapped[dict | list] = mapped_column(JSONB, nullable=False)
    refreshed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
