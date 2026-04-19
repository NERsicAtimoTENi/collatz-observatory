from __future__ import annotations

import sqlite3



import os
from pathlib import Path

DEFAULT_DB_PATH = Path(
    os.getenv(
        "DATABASE_PATH",
        str(Path(__file__).resolve().parent.parent / "data/collatz.db")
    )
)


def get_connection(db_path: str | Path | None = None) -> sqlite3.Connection:
    path = Path(db_path or DEFAULT_DB_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS numbers (
            n INTEGER PRIMARY KEY,
            steps_to_1 INTEGER NOT NULL,
            peak_value INTEGER NOT NULL,
            stopping_time INTEGER NOT NULL,
            peak_ratio REAL NOT NULL,
            is_record_steps INTEGER NOT NULL DEFAULT 0,
            is_record_peak INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS system_state (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            last_processed_n INTEGER NOT NULL,
            max_steps_seen INTEGER NOT NULL,
            max_peak_seen INTEGER NOT NULL
        )
        """
    )
    _ensure_column(connection, "numbers", "is_record_steps", "INTEGER NOT NULL DEFAULT 0")
    _ensure_column(connection, "numbers", "is_record_peak", "INTEGER NOT NULL DEFAULT 0")
    connection.commit()


def _ensure_column(connection: sqlite3.Connection, table_name: str, column_name: str, definition: str) -> None:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    existing_columns = {row["name"] for row in rows}
    if column_name not in existing_columns:
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {definition}")
