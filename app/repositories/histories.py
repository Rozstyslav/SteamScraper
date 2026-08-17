import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.database import connect
from app.models import History, HistoryList, HistoryMethod, HistorySummary


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def create(method: HistoryMethod, request: dict[str, Any]) -> str:
    history_id = str(uuid4())
    with connect() as connection:
        connection.execute(
            """
            INSERT INTO histories (id, method, request, status, started_at)
            VALUES (?, ?, ?, 'running', ?)
            """,
            (history_id, method, json.dumps(request, ensure_ascii=False), _now()),
        )
    return history_id


def finish(
    history_id: str,
    *,
    result: dict[str, Any] | None = None,
    error: str | None = None,) -> None:

    status = "failed" if error is not None else "succeeded"
    serialized_result = (
        json.dumps(result, ensure_ascii=False) if result is not None else None
    )
    with connect() as connection:
        connection.execute(
            """
            UPDATE histories
            SET status = ?, finished_at = ?, result = ?, error = ?
            WHERE id = ?
            """,
            (status, _now(), serialized_result, error, history_id),
        )


def list_all(limit: int, offset: int) -> HistoryList:
    with connect() as connection:
        total = connection.execute("SELECT COUNT(*) FROM histories").fetchone()[0]
        rows = connection.execute(
            """
            SELECT id, method, request, status, started_at, finished_at
            FROM histories
            ORDER BY started_at DESC, id DESC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
    return HistoryList(
        items=[
            HistorySummary(
                id=row["id"],
                method=row["method"],
                request=json.loads(row["request"]),
                status=row["status"],
                started_at=row["started_at"],
                finished_at=row["finished_at"],
            )
            for row in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


def find(history_id: str) -> History | None:
    with connect() as connection:
        row = connection.execute(
            "SELECT * FROM histories WHERE id = ?", (history_id,)
        ).fetchone()
    if row is None:
        return None
    return History(
        id=row["id"],
        method=row["method"],
        request=json.loads(row["request"]),
        status=row["status"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        result=json.loads(row["result"]) if row["result"] else None,
        error=row["error"],
    )
