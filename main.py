from typing import Annotated

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI()

STEAM_SEARCH_URL = "https://store.steampowered.com/api/storesearch/"


class GameSearchRequest(BaseModel):
    query: Annotated[str, Field(min_length=1, max_length=200)]
    limit: Annotated[int, Field(ge=1, le=20)] = 1


class Platforms(BaseModel):
    windows: bool = False
    mac: bool = False
    linux: bool = False


class GameSearchResult(BaseModel):
    app_id: int
    name: str
    url: str
    price: float | None = Field(
        default=None,
    )
    original_price: float | None = Field(
        default=None,
    )
    currency: str | None = None
    discount_percent: int | None = None
    image: str | None = None
    platforms: Platforms = Field(default_factory=Platforms)


class GameSearchResponse(BaseModel):
    query: str
    count: int
    results: list[GameSearchResult]


def convert_price(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return round(value / 100, 2)


@app.post("/api/v1/games/search", response_model=GameSearchResponse)
async def search_game(request: GameSearchRequest) -> GameSearchResponse:
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=422, detail="Query must not be blank")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                STEAM_SEARCH_URL,
                params={
                    "term": query,
                    "l": "ukrainian",
                    "cc": "ua",
                },
                headers={"User-Agent": "SteamScraper/1.0"},
            )
            response.raise_for_status()
            payload = response.json()

    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Steam request timed out") from exc

    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=502,
            detail="Steam returned an invalid response",
        ) from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise HTTPException(status_code=502, detail="Steam returned an invalid response")

    results: list[GameSearchResult] = []

    for item in payload["items"]:
        if len(results) >= request.limit:
            break

        if not isinstance(item, dict):
            continue

        app_id = item.get("id")
        name = item.get("name")

        if (
            isinstance(app_id, bool)
            or not isinstance(app_id, int)
            or not isinstance(name, str)
        ):
            continue

        if app_id == 0:
            raise HTTPException(status_code=404, detail="Game not found")

        price_data = item.get("price")

        if not isinstance(price_data, dict):
            price_data = {}

        platform_data = item.get("platforms")

        if not isinstance(platform_data, dict):
            platform_data = {}

        results.append(
            GameSearchResult(
                app_id=app_id,
                name=name,
                url=f"https://store.steampowered.com/app/{app_id}/",
                price=convert_price(price_data.get("final")),
                original_price=convert_price(price_data.get("initial")),
                currency=price_data.get("currency"),
                discount_percent=price_data.get("discount_percent"),
                image=item.get("tiny_image"),
                platforms=Platforms(
                    windows=bool(platform_data.get("windows")),
                    mac=bool(platform_data.get("mac")),
                    linux=bool(platform_data.get("linux")),
                ),
            )
        )

    if not results:
        raise HTTPException(status_code=404, detail="Game not found")

    return GameSearchResponse(query=query, count=len(results), results=results)

@app.post("/api/v1/games/details")
def detail_game(game_id: str):
    pass

@app.post("/api/v1/games/open")
def open_game(game_id: str):
    pass

@app.get("/api/v1/histories")
def histories(game_id: str):
    pass

@app.get("/api/v1/histories/{histories}")
def get_history(histories_id: str):
    pass
