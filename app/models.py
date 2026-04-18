from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NumberRecord:
    n: int
    steps_to_1: int
    peak_value: int
    stopping_time: int
    peak_ratio: float
    is_record_steps: bool = False
    is_record_peak: bool = False


@dataclass(frozen=True)
class SystemState:
    last_processed_n: int
    max_steps_seen: int
    max_peak_seen: int
