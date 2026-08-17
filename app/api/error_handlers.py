from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.exceptions import (
    BrowserOpenError,
    GameNotFoundError,
    SteamTimeoutError,
    SteamUpstreamError,
)


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(GameNotFoundError)
    async def game_not_found(
        _request: Request, exception: GameNotFoundError
    ) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exception)})

    @app.exception_handler(SteamTimeoutError)
    async def steam_timeout(
        _request: Request, exception: SteamTimeoutError
    ) -> JSONResponse:
        return JSONResponse(status_code=504, content={"detail": str(exception)})

    @app.exception_handler(SteamUpstreamError)
    async def steam_unavailable(
        _request: Request, exception: SteamUpstreamError
    ) -> JSONResponse:
        return JSONResponse(status_code=502, content={"detail": str(exception)})

    @app.exception_handler(BrowserOpenError)
    async def browser_unavailable(
        _request: Request, exception: BrowserOpenError
    ) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exception)})
