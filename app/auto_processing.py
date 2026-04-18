from __future__ import annotations

import threading
import time
from pathlib import Path

from app.batch import process_next_batch
from app.db import get_connection, init_db
from app.repository import NumberRepository


DEFAULT_AUTO_BATCH_SIZE = 100
DEFAULT_AUTO_SLEEP_SECONDS = 0.2


def parse_auto_processing_enabled(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def start_auto_processing_worker(
    db_path: str | Path,
    batch_size: int = DEFAULT_AUTO_BATCH_SIZE,
    sleep_seconds: float = DEFAULT_AUTO_SLEEP_SECONDS,
) -> tuple[threading.Thread, threading.Event]:
    stop_event = threading.Event()
    thread = threading.Thread(
        target=_run_auto_processing_loop,
        args=(Path(db_path), stop_event, batch_size, sleep_seconds),
        daemon=True,
        name="collatz-auto-processor",
    )
    thread.start()
    return thread, stop_event


def _run_auto_processing_loop(
    db_path: Path,
    stop_event: threading.Event,
    batch_size: int,
    sleep_seconds: float,
) -> None:
    connection = get_connection(db_path)
    try:
        init_db(connection)
        repository = NumberRepository(connection)
        while not stop_event.is_set():
            process_next_batch(repository, batch_size)
            stop_event.wait(sleep_seconds)
    finally:
        connection.close()
