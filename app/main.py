from __future__ import annotations

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Path as PathParam, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.auto_processing import (
    DEFAULT_AUTO_BATCH_SIZE,
    DEFAULT_AUTO_SLEEP_SECONDS,
    parse_auto_processing_enabled,
    start_auto_processing_worker,
)
from app.collatz import compute_collatz_detail
from app.db import DEFAULT_DB_PATH, get_connection, init_db
from app.models import NumberRecord, SystemState
from app.repository import NumberRepository
from app.schemas import NumberDetail, NumberListResponse, NumberMetrics, RecordsResponse, StatusResponse
from app.seed import seed_initial_numbers


BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def create_app(
    db_path: str | Path | None = None,
    seed_data: bool = True,
    auto_processing_enabled: bool | None = None,
    auto_batch_size: int = DEFAULT_AUTO_BATCH_SIZE,
    auto_sleep_seconds: float = DEFAULT_AUTO_SLEEP_SECONDS,
) -> FastAPI:
    resolved_db_path = str(Path(db_path or DEFAULT_DB_PATH))
    enable_auto_processing = (
        parse_auto_processing_enabled(os.getenv("ENABLE_AUTO_PROCESSING"))
        if auto_processing_enabled is None
        else auto_processing_enabled
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        connection = get_connection(resolved_db_path)
        init_db(connection)
        if seed_data:
            seed_initial_numbers(connection)
        app.state.db_connection = connection
        app.state.db_path = resolved_db_path
        app.state.auto_processing_running = False
        app.state.processing_batch_size = auto_batch_size if enable_auto_processing else None
        app.state.processing_sleep_seconds = auto_sleep_seconds if enable_auto_processing else None
        app.state.auto_processing_stop_event = None
        app.state.auto_processing_thread = None
        if enable_auto_processing:
            thread, stop_event = start_auto_processing_worker(
                db_path=resolved_db_path,
                batch_size=auto_batch_size,
                sleep_seconds=auto_sleep_seconds,
            )
            app.state.auto_processing_thread = thread
            app.state.auto_processing_stop_event = stop_event
            app.state.auto_processing_running = True
        yield
        stop_event = app.state.auto_processing_stop_event
        thread = app.state.auto_processing_thread
        if stop_event is not None:
            stop_event.set()
        if thread is not None:
            thread.join(timeout=2)
        app.state.auto_processing_running = False
        connection.close()

    app = FastAPI(title="Collatz Observatory", lifespan=lifespan)
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    def get_repository(request: Request) -> NumberRepository:
        return NumberRepository(request.app.state.db_connection)

    def ensure_number_record(repository: NumberRepository, n: int) -> NumberMetrics:
        existing = repository.get_number(n)
        if existing:
            return NumberMetrics.model_validate(existing)

        detail = compute_collatz_detail(n)
        record = NumberRecord(
            n=detail.metrics.n,
            steps_to_1=detail.metrics.steps_to_1,
            peak_value=detail.metrics.peak_value,
            stopping_time=detail.metrics.stopping_time,
            peak_ratio=detail.metrics.peak_ratio,
            is_record_steps=False,
            is_record_peak=False,
        )
        repository.upsert_number(record)
        return NumberMetrics.model_validate(record)

    @app.get("/", response_class=HTMLResponse)
    def index(
        request: Request,
        filter_mode: str = Query(default="all", pattern="^(all|record_steps|record_peaks)$"),
    ):
        repository = get_repository(request)
        recent_numbers = repository.list_numbers_by_filter(filter_mode=filter_mode, limit=20)
        top_steps = repository.list_top_by_steps(limit=10)
        top_peaks = repository.list_top_by_peak(limit=10)
        champion_steps = top_steps[0] if top_steps else None
        champion_peak = top_peaks[0] if top_peaks else None
        latest_numbers = repository.list_latest_numbers(limit=20)
        latest_step_records = repository.list_latest_step_records(limit=10)
        latest_peak_records = repository.list_latest_peak_records(limit=10)
        system_state = repository.get_system_state() or SystemState(
            last_processed_n=0,
            max_steps_seen=0,
            max_peak_seen=0,
        )
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "numbers": recent_numbers,
                "total_numbers_stored": repository.get_total(),
                "filtered_total": repository.get_filtered_total(filter_mode),
                "filter_mode": filter_mode,
                "top_steps": top_steps,
                "top_peaks": top_peaks,
                "champion_steps": champion_steps,
                "champion_peak": champion_peak,
                "latest_numbers": latest_numbers,
                "latest_step_records": latest_step_records,
                "latest_peak_records": latest_peak_records,
                "system_state": system_state,
            },
        )

    @app.get("/status", response_model=StatusResponse)
    def status(request: Request) -> StatusResponse:
        repository = get_repository(request)
        system_state = repository.get_system_state() or SystemState(
            last_processed_n=0,
            max_steps_seen=0,
            max_peak_seen=0,
        )
        return StatusResponse(
            status="ok",
            database_path=request.app.state.db_path,
            total_numbers_stored=repository.get_total(),
            last_processed_n=system_state.last_processed_n,
            max_steps_seen=system_state.max_steps_seen,
            max_peak_seen=system_state.max_peak_seen,
            auto_processing_running=request.app.state.auto_processing_running,
            processing_batch_size=request.app.state.processing_batch_size,
            processing_sleep_seconds=request.app.state.processing_sleep_seconds,
        )

    @app.get("/records", response_model=RecordsResponse)
    def records(request: Request) -> RecordsResponse:
        repository = get_repository(request)
        return RecordsResponse(
            step_records=[NumberMetrics.model_validate(item) for item in repository.list_step_records()],
            peak_records=[NumberMetrics.model_validate(item) for item in repository.list_peak_records()],
        )

    @app.get("/numbers", response_model=NumberListResponse)
    def list_numbers(
        request: Request,
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
    ) -> NumberListResponse:
        repository = get_repository(request)
        items = [NumberMetrics.model_validate(item) for item in repository.list_numbers(limit=limit, offset=offset)]
        return NumberListResponse(items=items, total=repository.get_total())

    @app.get("/numbers/{n}")
    def get_number_detail(request: Request, n: int = PathParam(..., ge=1)):
        repository = get_repository(request)
        metrics = ensure_number_record(repository, n)
        detail = compute_collatz_detail(n)
        accept_header = request.headers.get("accept", "")
        if "text/html" in accept_header and "application/json" not in accept_header:
            return templates.TemplateResponse(
                request=request,
                name="detail.html",
                context={
                    "metrics": metrics,
                    "sequence": detail.sequence,
                    "step_labels": list(range(len(detail.sequence))),
                    "use_log_scale": max(detail.sequence) >= 1000,
                },
            )
        return NumberDetail(**metrics.model_dump(), sequence=detail.sequence)

    return app


app = create_app()
