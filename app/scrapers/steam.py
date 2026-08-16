import httpx

from app.config import settings
from app.exceptions import GameNotFoundError, SteamUpstreamError
from app.models import GameSearchResult, Platforms


def _convert_price(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return round(value / 100, 2)


async def search_steam(query: str, limit: int) -> list[GameSearchResult]:
    try:
        async with httpx.AsyncClient(timeout=settings.steam_timeout_seconds) as client:
            response = await client.get(
                settings.steam_search_url,
                params={
                    "term": query,
                    "l": settings.steam_language,
                    "cc": settings.steam_country,
                },
                headers={"User-Agent": settings.user_agent},
            )
            response.raise_for_status()
            payload = response.json()
    except httpx.TimeoutException as exc:
        raise SteamUpstreamError("Steam request timed out") from exc
    except (httpx.HTTPError, ValueError) as exc:
        raise SteamUpstreamError("Steam returned an invalid response") from exc

    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise SteamUpstreamError("Steam returned an invalid response")

    results: list[GameSearchResult] = []
    for item in payload["items"]:
        if len(results) >= limit:
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
        if app_id <= 0:
            raise GameNotFoundError("Game not found")

        price = item.get("price")
        price = price if isinstance(price, dict) else {}
        platforms = item.get("platforms")
        platforms = platforms if isinstance(platforms, dict) else {}

        results.append(
            GameSearchResult(
                app_id=app_id,
                name=name,
                url=f"https://store.steampowered.com/app/{app_id}/",
                price=_convert_price(price.get("final")),
                original_price=_convert_price(price.get("initial")),
                currency=price.get("currency"),
                discount_percent=price.get("discount_percent"),
                image=item.get("tiny_image"),
                platforms=Platforms(
                    windows=bool(platforms.get("windows")),
                    mac=bool(platforms.get("mac")),
                    linux=bool(platforms.get("linux")),
                ),
            )
        )

    if not results:
        raise GameNotFoundError("Game not found")
    return results
