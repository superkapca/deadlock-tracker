from functools import lru_cache
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = Field(
        default="postgresql+asyncpg://user:password@localhost:5432/deadlock_tracker",
        alias="DATABASE_URL",
    )
    alembic_database_url: str | None = Field(default=None, alias="ALEMBIC_DATABASE_URL")
    deadlock_api_base_url: str = Field(default="https://api.deadlock-api.com", alias="DEADLOCK_API_BASE_URL")
    deadlock_api_key: str | None = Field(default=None, alias="DEADLOCK_API_KEY")
    cache_static_ttl_hours: int = Field(default=24, alias="CACHE_STATIC_TTL_HOURS")
    cache_player_ttl_minutes: int = Field(default=15, alias="CACHE_PLAYER_TTL_MINUTES")
    cache_match_ttl_hours: int = Field(default=24, alias="CACHE_MATCH_TTL_HOURS")
    cache_mmr_ttl_minutes: int = Field(default=60, alias="CACHE_MMR_TTL_MINUTES")
    http_timeout_seconds: float = Field(default=15, alias="HTTP_TIMEOUT_SECONDS")
    cors_origins: list[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        alias="CORS_ORIGINS",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: str | list[str]) -> list[str]:
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def async_database_url(self) -> str:
        return _normalize_asyncpg_url(self.database_url)

    @property
    def sync_database_url(self) -> str:
        url = self.alembic_database_url or self.database_url
        return _normalize_sync_postgres_url(url)


@lru_cache
def get_settings() -> Settings:
    return Settings()


def _normalize_asyncpg_url(url: str) -> str:
    normalized = url.replace("postgres://", "postgresql://", 1)
    if normalized.startswith("postgresql://"):
        normalized = normalized.replace("postgresql://", "postgresql+asyncpg://", 1)
    normalized = normalized.replace("sslmode=require", "ssl=require")
    return _remove_query_params(normalized, {"channel_binding"})


def _normalize_sync_postgres_url(url: str) -> str:
    normalized = url.replace("postgres://", "postgresql://", 1)
    normalized = normalized.replace("postgresql+asyncpg://", "postgresql://", 1)
    if normalized.startswith("postgresql://"):
        normalized = normalized.replace("postgresql://", "postgresql+psycopg://", 1)
    return normalized.replace("ssl=require", "sslmode=require")


def _remove_query_params(url: str, names: set[str]) -> str:
    parts = urlsplit(url)
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True) if key not in names]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))
