from __future__ import annotations

from app.batch import process_next_batch
from app.db import get_connection, init_db
from app.repository import NumberRepository


def test_process_first_batch_starts_at_one_and_updates_state(tmp_path):
    connection = get_connection(tmp_path / "batch.db")
    try:
        init_db(connection)
        repository = NumberRepository(connection)

        result = process_next_batch(repository, 3)

        assert result.start_n == 1
        assert result.end_n == 3
        assert result.processed_count == 3
        assert result.last_processed_n == 3
        assert result.max_steps_seen == 7
        assert result.max_peak_seen == 16

        state = repository.get_system_state()
        assert state is not None
        assert state.last_processed_n == 3
        assert state.max_steps_seen == 7
        assert state.max_peak_seen == 16

        first = repository.get_number(1)
        second = repository.get_number(2)
        third = repository.get_number(3)
        assert first is not None and first.is_record_steps is False and first.is_record_peak is True
        assert second is not None and second.is_record_steps is True and second.is_record_peak is True
        assert third is not None and third.is_record_steps is True and third.is_record_peak is True
    finally:
        connection.close()


def test_process_second_batch_resumes_from_last_processed_number(tmp_path):
    connection = get_connection(tmp_path / "batch.db")
    try:
        init_db(connection)
        repository = NumberRepository(connection)

        process_next_batch(repository, 3)
        result = process_next_batch(repository, 3)

        assert result.start_n == 4
        assert result.end_n == 6
        assert result.last_processed_n == 6
        assert result.max_steps_seen == 8
        assert result.max_peak_seen == 16

        fourth = repository.get_number(4)
        fifth = repository.get_number(5)
        sixth = repository.get_number(6)
        assert fourth is not None and fourth.is_record_steps is False and fourth.is_record_peak is False
        assert fifth is not None and fifth.is_record_steps is False and fifth.is_record_peak is False
        assert sixth is not None and sixth.is_record_steps is True and sixth.is_record_peak is False
    finally:
        connection.close()
