from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class UpstreamError(Exception):
    status_code = 502

    def __init__(self, message: str = "Upstream API error") -> None:
        self.message = message
        super().__init__(message)


class UpstreamNotFound(UpstreamError):
    status_code = 404


class UpstreamRateLimited(UpstreamError):
    status_code = 503


class UpstreamTimeout(UpstreamError):
    status_code = 504


def register_exception_handlers(app: FastAPI) -> None:
    async def upstream_handler(_: Request, exc: UpstreamError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})

    app.add_exception_handler(UpstreamError, upstream_handler)  # type: ignore[arg-type]
