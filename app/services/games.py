import asyncio

from app.models import GameDetailsResponse, GameSearchResponse, OpenGameResponse
from app.scrapers.browser import steam_browser
from app.scrapers.steam import search_steam


async def search_games(query: str, limit: int) -> GameSearchResponse:
    normalized_query = query.strip()
    results = await search_steam(normalized_query, limit)
    return GameSearchResponse(
        query=normalized_query,
        count=len(results),
        results=results,
    )


async def find_and_open_game(name: str) -> OpenGameResponse:
    normalized_name = name.strip()
    search_response = await search_games(normalized_name, limit=20)

    game = next(
        (
            result
            for result in search_response.results
            if result.name.strip().casefold() == normalized_name.casefold()
        ),
        search_response.results[0],
    )

    await asyncio.to_thread(steam_browser.open, game.url)
    return OpenGameResponse(status="opened", app_id=game.app_id, url=game.url)


async def get_game_details(name: str, reviews_count: int) -> GameDetailsResponse:
    normalized_name = name.strip()
    search_response = await search_games(normalized_name, limit=20)
    game = next(
        (
            result
            for result in search_response.results
            if result.name.strip().casefold() == normalized_name.casefold()
        ),
        search_response.results[0],
    )
    return await asyncio.to_thread(
        steam_browser.scrape_details, game.app_id, game.url, reviews_count
    )
