from datetime import datetime
from typing import Annotated, Any, Literal

from pydantic import BaseModel, Field, StringConstraints

SearchText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
]


class GameSearchRequest(BaseModel):
    query: SearchText
    limit: Annotated[int, Field(ge=1, le=20)] = 1


class Platforms(BaseModel):
    windows: bool = False
    mac: bool = False
    linux: bool = False


class GameSearchResult(BaseModel):
    app_id: int
    name: str
    url: str
    price: float | None = None
    original_price: float | None = None
    currency: str | None = None
    discount_percent: int | None = None
    image: str | None = None
    platforms: Platforms = Field(default_factory=Platforms)


class GameSearchResponse(BaseModel):
    query: str
    count: int
    results: list[GameSearchResult]


class OpenGameRequest(BaseModel):
    name: SearchText


class OpenGameResponse(BaseModel):
    status: Literal["opened"]
    app_id: int
    url: str


class GameDetailsRequest(BaseModel):
    name: SearchText
    reviews_count: Annotated[int, Field(ge=3, le=50)] = 3


class GameReview(BaseModel):
    text: str
    recommended: bool
    published_at: str
    playtime: str | None = None


class GameDetailsResponse(BaseModel):
    app_id: int
    name: str
    url: str
    developer: str | None = None
    publisher: str | None = None
    release_date: str | None = None
    price: str | None = None
    is_free: bool = False
    short_description: str | None = None
    user_score: str | None = None
    reviews: list[GameReview]


HistoryMethod = Literal["http", "headless", "non_headless"]
HistoryStatus = Literal["running", "succeeded", "failed"]


class History(BaseModel):
    id: str
    method: HistoryMethod
    request: dict[str, Any]
    status: HistoryStatus
    started_at: datetime
    finished_at: datetime | None = None
    result: dict[str, Any] | None = None
    error: str | None = None


class HistorySummary(BaseModel):
    id: str
    method: HistoryMethod
    request: dict[str, Any]
    status: HistoryStatus
    started_at: datetime
    finished_at: datetime | None = None


class HistoryList(BaseModel):
    items: list[HistorySummary]
    total: int
    limit: int
    offset: int
