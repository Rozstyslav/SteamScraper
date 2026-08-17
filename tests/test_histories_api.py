from dataclasses import replace
from unittest.mock import AsyncMock

import pytest
from fastapi.testclient import TestClient

import app.database as database_module
from app.config import settings
from app.exceptions import GameNotFoundError
from app.models import GameSearchResponse
from main import app


@pytest.fixture
def client(tmp_path, monkeypatch):
    test_settings = replace(settings, database_path=str(tmp_path / "test.sqlite3"))
    monkeypatch.setattr(database_module, "settings", test_settings)
    with TestClient(app) as test_client:
        yield test_client


def test_successful_execution_is_available_in_history(client, monkeypatch):
    search = AsyncMock(
        return_value=GameSearchResponse(query="portal", count=0, results=[])
    )
    monkeypatch.setattr("app.api.routes.games.search_games", search)

    response = client.post(
        "/api/v1/games/search",
        json={"query": "portal", "limit": 1},
    )

    assert response.status_code == 200
    history_list = client.get("/api/v1/histories").json()
    assert history_list["total"] == 1
    summary = history_list["items"][0]
    assert summary["method"] == "http"
    assert summary["status"] == "succeeded"
    assert "result" not in summary
    assert "error" not in summary

    detail = client.get(f"/api/v1/histories/{summary['id']}").json()
    assert detail["result"] == response.json()
    assert detail["error"] is None


def test_failed_execution_stores_error(client, monkeypatch):
    search = AsyncMock(side_effect=GameNotFoundError("Game not found"))
    monkeypatch.setattr("app.api.routes.games.search_games", search)

    response = client.post(
        "/api/v1/games/search",
        json={"query": "missing", "limit": 1},
    )

    assert response.status_code == 404
    summary = client.get("/api/v1/histories").json()["items"][0]
    detail = client.get(f"/api/v1/histories/{summary['id']}").json()
    assert detail["status"] == "failed"
    assert detail["result"] is None
    assert detail["error"] == "Game not found"


def test_missing_history_returns_404(client):
    response = client.get("/api/v1/histories/unknown")

    assert response.status_code == 404
    assert response.json() == {"detail": "History not found"}
