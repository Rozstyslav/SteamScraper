from typing import Annotated, Literal

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
