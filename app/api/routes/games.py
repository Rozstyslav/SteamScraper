from fastapi import APIRouter, HTTPException

from app.exceptions import BrowserOpenError, GameNotFoundError, SteamUpstreamError
from app.models import (
    GameSearchRequest,
    GameSearchResponse,
    OpenGameRequest,
    OpenGameResponse,
)
from app.services.games import find_and_open_game, search_games

router = APIRouter(prefix="/api/v1/games", tags=["games"])


@router.post("/search", response_model=GameSearchResponse)
async def search_game(request: GameSearchRequest) -> GameSearchResponse:
    try:
        return await search_games(request.query, request.limit)
    except GameNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SteamUpstreamError as exc:
        status_code = 504 if "timed out" in str(exc) else 502
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc


@router.post("/open", response_model=OpenGameResponse)
async def open_game(request: OpenGameRequest) -> OpenGameResponse:
    try:
        return await find_and_open_game(request.name)
    except GameNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except SteamUpstreamError as exc:
        status_code = 504 if "timed out" in str(exc) else 502
        raise HTTPException(status_code=status_code, detail=str(exc)) from exc
    except BrowserOpenError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@router.post("/details")
def detail_game(game_id: str):
    pass
