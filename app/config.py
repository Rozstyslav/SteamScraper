import os
from dataclasses import dataclass, field


def _env_float(name: str, default: float) -> float:
    return float(os.getenv(name, default))


def _env_int(name: str, default: int) -> int:
    return int(os.getenv(name, default))


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().casefold() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    steam_search_url: str = field(
        default_factory=lambda: os.getenv(
            "STEAM_SEARCH_URL", "https://store.steampowered.com/api/storesearch/"
        )
    )
    steam_language: str = field(
        default_factory=lambda: os.getenv("STEAM_LANGUAGE", "ukrainian")
    )
    steam_country: str = field(
        default_factory=lambda: os.getenv("STEAM_COUNTRY", "ua")
    )
    steam_timeout_seconds: float = field(
        default_factory=lambda: _env_float("STEAM_TIMEOUT_SECONDS", 10.0)
    )
    user_agent: str = field(
        default_factory=lambda: os.getenv("USER_AGENT", "SteamScraper/1.0")
    )
    database_path: str = field(
        default_factory=lambda: os.getenv("DATABASE_PATH", "steam_scraper.sqlite3")
    )
    database_timeout_seconds: float = field(
        default_factory=lambda: _env_float("DATABASE_TIMEOUT_SECONDS", 10.0)
    )
    browser_headless: bool = field(
        default_factory=lambda: _env_bool("BROWSER_HEADLESS", True)
    )
    browser_language: str = field(
        default_factory=lambda: os.getenv("BROWSER_LANGUAGE", "uk-UA")
    )
    browser_binary: str | None = field(
        default_factory=lambda: os.getenv("BROWSER_BINARY") or None
    )
    browser_accept_languages: str = field(
        default_factory=lambda: os.getenv(
            "BROWSER_ACCEPT_LANGUAGES", "uk-UA,uk,en-US,en"
        )
    )
    browser_window_size: str = field(
        default_factory=lambda: os.getenv("BROWSER_WINDOW_SIZE", "1920,1080")
    )
    browser_page_load_timeout_seconds: float = field(
        default_factory=lambda: _env_float("BROWSER_PAGE_LOAD_TIMEOUT_SECONDS", 30.0)
    )
    browser_wait_timeout_seconds: float = field(
        default_factory=lambda: _env_float("BROWSER_WAIT_TIMEOUT_SECONDS", 25.0)
    )
    browser_age_gate_year: int = field(
        default_factory=lambda: _env_int("BROWSER_AGE_GATE_YEAR", 1990)
    )


settings = Settings()
