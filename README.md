# Collatz Observatory

A small FastAPI application that computes Collatz metrics for natural numbers, stores the core metrics in SQLite, and exposes both a JSON API and a server-rendered frontend.

## Features

- SQLite-backed storage in `data/collatz.db`
- Core metrics per number:
  - `n`
  - `steps_to_1`
  - `peak_value`
  - `stopping_time`
  - `peak_ratio`
- Full Collatz sequence returned on demand from `GET /numbers/{n}`
- Minimal server-rendered frontend at `/`

## Metric definitions

- `steps_to_1`: number of steps needed to reach `1`
- `stopping_time`: number of steps until the sequence first reaches a value less than the starting `n`
- `peak_ratio`: `peak_value / n`

## API

- `GET /status`
- `GET /numbers`
- `GET /numbers/{n}`

## Development

Install dependencies:

```bash
python3 -m pip install -e '.[dev]'
```

Run the server:

```bash
python3 -m uvicorn app.main:app --reload
```

Enable automatic background processing at startup:

```bash
ENABLE_AUTO_PROCESSING=true python3 -m uvicorn app.main:app --reload
```

Run tests:

```bash
python3 -m pytest
```

Process the next batch of numbers:

```bash
python3 -m app.cli 100
```
