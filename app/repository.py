from __future__ import annotations

import sqlite3

from app.models import NumberRecord, SystemState


class NumberRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection

    def get_total(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) AS total FROM numbers").fetchone()
        return int(row["total"])

    def list_numbers(self, limit: int = 50, offset: int = 0) -> list[NumberRecord]:
        rows = self.connection.execute(
            """
            SELECT n, steps_to_1, peak_value, stopping_time, peak_ratio, is_record_steps, is_record_peak
            FROM numbers
            ORDER BY n ASC
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        ).fetchall()
        return [self._to_record(row) for row in rows]

    def list_numbers_by_filter(self, filter_mode: str, limit: int = 50, offset: int = 0) -> list[NumberRecord]:
        if filter_mode == "record_steps":
            query = """
                SELECT n, steps_to_1, peak_value, stopping_time, peak_ratio, is_record_steps, is_record_peak
                FROM numbers
                WHERE is_record_steps = 1
                ORDER BY n ASC
                LIMIT ? OFFSET ?
            """
        elif filter_mode == "record_peaks":
            query = """
                SELECT n, steps_to_1, peak_value, stopping_time, peak_ratio, is_record_steps, is_record_peak
                FROM numbers
                WHERE is_record_peak = 1
                ORDER BY n ASC
                LIMIT ? OFFSET ?
            """
        else:
            query = """
                SELECT n, steps_to_1, peak_value, stopping_time, peak_ratio, is_record_steps, is_record_peak
                FROM numbers
                ORDER BY n ASC
                LIMIT ? OFFSET ?
            """

        rows = self.connection.execute(query, (limit, offset)).fetchall()
        return [self._to_record(row) for row in rows]

    def get_filtered_total(self, filter_mode: str) -> int:
        if filter_mode == "record_steps":
            row = self.connection.execute(
                "SELECT COUNT(*) AS total FROM numbers WHERE is_record_steps = 1"
            ).fetchone()
        elif filter_mode == "record_peaks":
            row = self.connection.execute(
                "SELECT COUNT(*) AS total FROM numbers WHERE is_record_peak = 1"
            ).fetchone()
        else:
            row = self.connection.execute("SELECT COUNT(*) AS total FROM numbers").fetchone()
        return int(row["total"])

    def list_step_records(self) -> list[NumberRecord]:
        rows = self.connection.execute(
            """
            SELECT n, steps_to_1, peak_value, stopping_time, peak_ratio, is_record_steps, is_record_peak
            FROM numbers
            WHERE is_record_steps = 1
            ORDER BY n ASC
            """
        ).fetchall()
        return [self._to_record(row) for row in rows]

    def list_top_by_steps(self, limit: int = 10) -> list[NumberRecord]:
        rows = self.connection.execute(
            """
            SELECT n, steps_to_1, peak_value, stopping_time, peak_ratio, is_record_steps, is_record_peak
            FROM numbers
            ORDER BY steps_to_1 DESC, n ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [self._to_record(row) for row in rows]

    def list_top_by_peak(self, limit: int = 10) -> list[NumberRecord]:
        rows = self.connection.execute(
            """
            SELECT n, steps_to_1, peak_value, stopping_time, peak_ratio, is_record_steps, is_record_peak
            FROM numbers
            ORDER BY peak_value DESC, n ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [self._to_record(row) for row in rows]

    def list_latest_numbers(self, limit: int = 20) -> list[NumberRecord]:
        rows = self.connection.execute(
            """
            SELECT n, steps_to_1, peak_value, stopping_time, peak_ratio, is_record_steps, is_record_peak
            FROM numbers
            ORDER BY n DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [self._to_record(row) for row in rows]

    def list_latest_step_records(self, limit: int = 10) -> list[NumberRecord]:
        rows = self.connection.execute(
            """
            SELECT n, steps_to_1, peak_value, stopping_time, peak_ratio, is_record_steps, is_record_peak
            FROM numbers
            WHERE is_record_steps = 1
            ORDER BY n DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [self._to_record(row) for row in rows]

    def list_latest_peak_records(self, limit: int = 10) -> list[NumberRecord]:
        rows = self.connection.execute(
            """
            SELECT n, steps_to_1, peak_value, stopping_time, peak_ratio, is_record_steps, is_record_peak
            FROM numbers
            WHERE is_record_peak = 1
            ORDER BY n DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [self._to_record(row) for row in rows]

    def list_peak_records(self) -> list[NumberRecord]:
        rows = self.connection.execute(
            """
            SELECT n, steps_to_1, peak_value, stopping_time, peak_ratio, is_record_steps, is_record_peak
            FROM numbers
            WHERE is_record_peak = 1
            ORDER BY n ASC
            """
        ).fetchall()
        return [self._to_record(row) for row in rows]

    def get_number(self, n: int) -> NumberRecord | None:
        row = self.connection.execute(
            """
            SELECT n, steps_to_1, peak_value, stopping_time, peak_ratio, is_record_steps, is_record_peak
            FROM numbers
            WHERE n = ?
            """,
            (n,),
        ).fetchone()
        return self._to_record(row) if row else None

    def upsert_number(self, record: NumberRecord) -> NumberRecord:
        self.connection.execute(
            """
            INSERT INTO numbers (
                n, steps_to_1, peak_value, stopping_time, peak_ratio, is_record_steps, is_record_peak
            )
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(n) DO UPDATE SET
                steps_to_1 = excluded.steps_to_1,
                peak_value = excluded.peak_value,
                stopping_time = excluded.stopping_time,
                peak_ratio = excluded.peak_ratio,
                is_record_steps = excluded.is_record_steps,
                is_record_peak = excluded.is_record_peak
            """,
            (
                record.n,
                record.steps_to_1,
                record.peak_value,
                record.stopping_time,
                record.peak_ratio,
                int(record.is_record_steps),
                int(record.is_record_peak),
            ),
        )
        self.connection.commit()
        return record

    def get_system_state(self) -> SystemState | None:
        row = self.connection.execute(
            """
            SELECT last_processed_n, max_steps_seen, max_peak_seen
            FROM system_state
            WHERE id = 1
            """
        ).fetchone()
        if row is None:
            return None
        return SystemState(
            last_processed_n=int(row["last_processed_n"]),
            max_steps_seen=int(row["max_steps_seen"]),
            max_peak_seen=int(row["max_peak_seen"]),
        )

    def upsert_system_state(self, state: SystemState) -> SystemState:
        self.connection.execute(
            """
            INSERT INTO system_state (id, last_processed_n, max_steps_seen, max_peak_seen)
            VALUES (1, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                last_processed_n = excluded.last_processed_n,
                max_steps_seen = excluded.max_steps_seen,
                max_peak_seen = excluded.max_peak_seen
            """,
            (state.last_processed_n, state.max_steps_seen, state.max_peak_seen),
        )
        self.connection.commit()
        return state

    @staticmethod
    def _to_record(row: sqlite3.Row) -> NumberRecord:
        return NumberRecord(
            n=int(row["n"]),
            steps_to_1=int(row["steps_to_1"]),
            peak_value=int(row["peak_value"]),
            stopping_time=int(row["stopping_time"]),
            peak_ratio=float(row["peak_ratio"]),
            is_record_steps=bool(row["is_record_steps"]),
            is_record_peak=bool(row["is_record_peak"]),
        )
