import sqlite3
from pathlib import Path

from app.config import settings


def connect() -> sqlite3.Connection:
    database_path = Path(settings.database_path)
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(
        database_path,
        timeout=settings.database_timeout_seconds,
    )
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    return connection


def initialize_database() -> None:
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS histories (
                id TEXT PRIMARY KEY,
                method TEXT NOT NULL
                    CHECK (method IN ('http', 'headless', 'non_headless')),
                request TEXT NOT NULL,
                status TEXT NOT NULL
                    CHECK (status IN ('running', 'succeeded', 'failed')),
                started_at TEXT NOT NULL,
                finished_at TEXT,
                result TEXT,
                error TEXT
            )
            """
        )
