from __future__ import annotations

from dataclasses import dataclass

from app.collatz import compute_collatz_metrics
from app.models import NumberRecord, SystemState
from app.repository import NumberRepository


@dataclass(frozen=True)
class BatchResult:
    start_n: int
    end_n: int
    processed_count: int
    last_processed_n: int
    max_steps_seen: int
    max_peak_seen: int


def process_next_batch(repository: NumberRepository, count: int) -> BatchResult:
    if count < 1:
        raise ValueError("count must be at least 1")

    state = repository.get_system_state() or SystemState(
        last_processed_n=0,
        max_steps_seen=0,
        max_peak_seen=0,
    )

    start_n = state.last_processed_n + 1
    current_state = state

    for n in range(start_n, start_n + count):
        metrics = compute_collatz_metrics(n)
        is_record_steps = metrics.steps_to_1 > current_state.max_steps_seen
        is_record_peak = metrics.peak_value > current_state.max_peak_seen

        repository.upsert_number(
            NumberRecord(
                n=metrics.n,
                steps_to_1=metrics.steps_to_1,
                peak_value=metrics.peak_value,
                stopping_time=metrics.stopping_time,
                peak_ratio=metrics.peak_ratio,
                is_record_steps=is_record_steps,
                is_record_peak=is_record_peak,
            )
        )

        current_state = SystemState(
            last_processed_n=n,
            max_steps_seen=metrics.steps_to_1 if is_record_steps else current_state.max_steps_seen,
            max_peak_seen=metrics.peak_value if is_record_peak else current_state.max_peak_seen,
        )
        repository.upsert_system_state(current_state)

    return BatchResult(
        start_n=start_n,
        end_n=current_state.last_processed_n,
        processed_count=count,
        last_processed_n=current_state.last_processed_n,
        max_steps_seen=current_state.max_steps_seen,
        max_peak_seen=current_state.max_peak_seen,
    )
