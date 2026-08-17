from fastapi import APIRouter

from app.models import (
    GameSearchRequest,
    GameSearchResponse,
    GameDetailsRequest,
    GameDetailsResponse,
    OpenGameRequest,
    OpenGameResponse,
)
from app.services.games import find_and_open_game, get_game_details, search_games
from app.services.histories import execute_with_history

router = APIRouter(prefix="/api/v1/games", tags=["games"])


@router.post("/search", response_model=GameSearchResponse)
async def search_game(request: GameSearchRequest) -> GameSearchResponse:
    return await execute_with_history(
        "http", request, lambda: search_games(request.query, request.limit)
    )


@router.post("/open", response_model=OpenGameResponse)
async def open_game(request: OpenGameRequest) -> OpenGameResponse:
    return await execute_with_history(
        "non_headless", request, lambda: find_and_open_game(request.name)
    )


@router.post("/details", response_model=GameDetailsResponse)
async def detail_game(request: GameDetailsRequest) -> GameDetailsResponse:
    return await execute_with_history(
        "headless",
        request,
        lambda: get_game_details(request.name, request.reviews_count),
    )
