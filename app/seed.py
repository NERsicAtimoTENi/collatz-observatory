from __future__ import annotations

import sqlite3

from app.collatz import compute_collatz_metrics
from app.models import NumberRecord
from app.repository import NumberRepository


def seed_initial_numbers(connection: sqlite3.Connection, upper_bound: int = 10) -> None:
    repository = NumberRepository(connection)
    if repository.get_total() > 0:
        return

    for n in range(1, upper_bound + 1):
        metrics = compute_collatz_metrics(n)
        repository.upsert_number(
            NumberRecord(
                n=metrics.n,
                steps_to_1=metrics.steps_to_1,
                peak_value=metrics.peak_value,
                stopping_time=metrics.stopping_time,
                peak_ratio=metrics.peak_ratio,
            )
        )
