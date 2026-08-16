from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    steam_search_url: str = "https://store.steampowered.com/api/storesearch/"
    steam_language: str = "ukrainian"
    steam_country: str = "ua"
    steam_timeout_seconds: float = 10.0
    user_agent: str = "SteamScraper/1.0"


settings = Settings()
