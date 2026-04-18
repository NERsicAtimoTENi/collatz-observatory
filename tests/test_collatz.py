from __future__ import annotations

import math

from app.collatz import compute_collatz_detail


def test_n_1_metrics():
    detail = compute_collatz_detail(1)

    assert detail.metrics.n == 1
    assert detail.metrics.steps_to_1 == 0
    assert detail.metrics.peak_value == 1
    assert detail.metrics.stopping_time == 0
    assert detail.metrics.peak_ratio == 1.0
    assert detail.sequence == [1]


def test_n_2_metrics():
    detail = compute_collatz_detail(2)

    assert detail.metrics.n == 2
    assert detail.metrics.steps_to_1 == 1
    assert detail.metrics.peak_value == 2
    assert detail.metrics.stopping_time == 1
    assert detail.metrics.peak_ratio == 1.0
    assert detail.sequence == [2, 1]


def test_n_3_metrics():
    detail = compute_collatz_detail(3)

    assert detail.metrics.n == 3
    assert detail.metrics.steps_to_1 == 7
    assert detail.metrics.peak_value == 16
    assert detail.metrics.stopping_time == 6
    assert math.isclose(detail.metrics.peak_ratio, 16 / 3)
    assert detail.sequence == [3, 10, 5, 16, 8, 4, 2, 1]


def test_n_27_metrics():
    detail = compute_collatz_detail(27)

    assert detail.metrics.n == 27
    assert detail.metrics.steps_to_1 == 111
    assert detail.metrics.peak_value == 9232
    assert detail.metrics.stopping_time == 96
    assert math.isclose(detail.metrics.peak_ratio, 9232 / 27)
    assert detail.sequence[0] == 27
    assert detail.sequence[-1] == 1
    assert len(detail.sequence) == 112
