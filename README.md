# deadlock-tracker

FastAPI backend for a Deadlock gameplay tracker. It uses NeonDB/Postgres as a persistent cache in front of `https://api.deadlock-api.com`.

## Setup

Create a virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
```

Create `.env`:

```env
DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST.neon.tech/DB?ssl=require
ALEMBIC_DATABASE_URL=postgresql+asyncpg://USER:PASSWORD@HOST.neon.tech/DB?ssl=require
DEADLOCK_API_BASE_URL=https://api.deadlock-api.com
DEADLOCK_API_KEY=
CACHE_STATIC_TTL_HOURS=24
CACHE_PLAYER_TTL_MINUTES=15
CACHE_MATCH_TTL_HOURS=24
CACHE_MMR_TTL_MINUTES=60
HTTP_TIMEOUT_SECONDS=15
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173
```

Use Neon's pooled connection string for `DATABASE_URL` in deployed app traffic when available. Use a direct connection string for `ALEMBIC_DATABASE_URL` if Neon provides separate pooled and direct URLs.

Run migrations:

```powershell
alembic upgrade head
```

Start the API:

```powershell
uvicorn main:app --reload
```

## Routes

```txt
GET /api/v1/health
GET /api/v1/players/search?q={query}
GET /api/v1/players/{account_id}
GET /api/v1/players/{account_id}/summary
GET /api/v1/players/{account_id}/matches
GET /api/v1/players/{account_id}/hero-stats
GET /api/v1/players/{account_id}/rank
GET /api/v1/players/{account_id}/mmr-history
GET /api/v1/matches/{match_id}
GET /api/v1/assets/heroes
GET /api/v1/assets/items
GET /api/v1/assets/ranks
```

## Tests

```powershell
pytest
```
