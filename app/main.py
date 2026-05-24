from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import assets, health, matches, players
from app.core.config import get_settings
from app.core.errors import register_exception_handlers
from app.services.deadlock_client import close_deadlock_client


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await close_deadlock_client()


app = FastAPI(title="Deadlock Tracker API", version="0.1.0", lifespan=lifespan)
settings = get_settings()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(players.router, prefix="/api/v1/players", tags=["players"])
app.include_router(matches.router, prefix="/api/v1/matches", tags=["matches"])
app.include_router(assets.router, prefix="/api/v1/assets", tags=["assets"])

register_exception_handlers(app)
