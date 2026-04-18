from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class NumberMetrics(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    n: int = Field(..., ge=1)
    steps_to_1: int = Field(..., ge=0)
    peak_value: int = Field(..., ge=1)
    stopping_time: int = Field(..., ge=0)
    peak_ratio: float = Field(..., ge=1.0)
    is_record_steps: bool = False
    is_record_peak: bool = False


class NumberDetail(NumberMetrics):
    sequence: list[int]


class NumberListResponse(BaseModel):
    items: list[NumberMetrics]
    total: int


class StatusResponse(BaseModel):
    status: str
    database_path: str
    total_numbers_stored: int
    last_processed_n: int
    max_steps_seen: int
    max_peak_seen: int
    auto_processing_running: bool
    processing_batch_size: int | None = None
    processing_sleep_seconds: float | None = None


class RecordsResponse(BaseModel):
    step_records: list[NumberMetrics]
    peak_records: list[NumberMetrics]
