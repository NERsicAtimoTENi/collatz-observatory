from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CollatzMetrics:
    n: int
    steps_to_1: int
    peak_value: int
    stopping_time: int
    peak_ratio: float


@dataclass(frozen=True)
class CollatzDetail:
    metrics: CollatzMetrics
    sequence: list[int]


def compute_collatz_detail(n: int) -> CollatzDetail:
    if n < 1:
        raise ValueError("n must be a positive integer")

    current = n
    steps_to_1 = 0
    peak_value = n
    stopping_time: int | None = None
    sequence = [n]

    while current != 1:
        if current % 2 == 0:
            current //= 2
        else:
            current = (3 * current) + 1

        steps_to_1 += 1
        peak_value = max(peak_value, current)
        sequence.append(current)

        if stopping_time is None and current < n:
            stopping_time = steps_to_1

    metrics = CollatzMetrics(
        n=n,
        steps_to_1=steps_to_1,
        peak_value=peak_value,
        stopping_time=stopping_time or 0,
        peak_ratio=peak_value / n,
    )
    return CollatzDetail(metrics=metrics, sequence=sequence)


def compute_collatz_metrics(n: int) -> CollatzMetrics:
    return compute_collatz_detail(n).metrics
