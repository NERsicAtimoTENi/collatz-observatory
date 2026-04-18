from __future__ import annotations

import math

from app.batch import process_next_batch
from app.repository import NumberRepository


def test_status_endpoint(client):
    response = client.get("/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["total_numbers_stored"] == 0
    assert payload["last_processed_n"] == 0
    assert payload["max_steps_seen"] == 0
    assert payload["max_peak_seen"] == 0
    assert payload["auto_processing_running"] is False
    assert payload["processing_batch_size"] is None
    assert payload["processing_sleep_seconds"] is None
    assert payload["database_path"].endswith("test_collatz.db")


def test_numbers_endpoint_starts_empty(client):
    response = client.get("/numbers")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 0
    assert payload["items"] == []


def test_numbers_detail_computes_and_persists_metrics(client):
    response = client.get("/numbers/3")

    assert response.status_code == 200
    payload = response.json()
    assert payload["n"] == 3
    assert payload["steps_to_1"] == 7
    assert payload["peak_value"] == 16
    assert payload["stopping_time"] == 6
    assert math.isclose(payload["peak_ratio"], 16 / 3)
    assert payload["is_record_steps"] is False
    assert payload["is_record_peak"] is False
    assert payload["sequence"] == [3, 10, 5, 16, 8, 4, 2, 1]

    list_response = client.get("/numbers")
    list_payload = list_response.json()
    assert list_payload["total"] == 1
    assert list_payload["items"][0]["n"] == 3


def test_numbers_detail_for_27_returns_full_sequence(client):
    response = client.get("/numbers/27")

    assert response.status_code == 200
    payload = response.json()
    assert payload["n"] == 27
    assert payload["steps_to_1"] == 111
    assert payload["peak_value"] == 9232
    assert payload["stopping_time"] == 96
    assert math.isclose(payload["peak_ratio"], 9232 / 27)
    assert payload["is_record_steps"] is False
    assert payload["is_record_peak"] is False
    assert payload["sequence"][0] == 27
    assert payload["sequence"][-1] == 1
    assert len(payload["sequence"]) == 112


def test_numbers_detail_html_page_renders_chart(client):
    response = client.get("/numbers/27", headers={"accept": "text/html"})

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "cdn.jsdelivr.net/npm/chart.js" in response.text
    assert 'id="collatz-chart"' in response.text
    assert "Y-axis uses a logarithmic scale." in response.text
    assert "27 -&gt; 82 -&gt; 41" in response.text


def test_status_returns_processing_state_after_batch(client):
    repository = NumberRepository(client.app.state.db_connection)
    process_next_batch(repository, 6)

    response = client.get("/status")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_numbers_stored"] == 6
    assert payload["last_processed_n"] == 6
    assert payload["max_steps_seen"] == 8
    assert payload["max_peak_seen"] == 16
    assert payload["auto_processing_running"] is False
    assert payload["processing_batch_size"] is None
    assert payload["processing_sleep_seconds"] is None


def test_records_endpoint_returns_step_and_peak_record_lists(client):
    repository = NumberRepository(client.app.state.db_connection)
    process_next_batch(repository, 7)

    response = client.get("/records")

    assert response.status_code == 200
    payload = response.json()
    assert [item["n"] for item in payload["step_records"]] == [2, 3, 6, 7]
    assert [item["n"] for item in payload["peak_records"]] == [1, 2, 3, 7]
    assert all(item["is_record_steps"] for item in payload["step_records"])
    assert all(item["is_record_peak"] for item in payload["peak_records"])


def test_homepage_shows_leaderboards_and_filter_links(client):
    repository = NumberRepository(client.app.state.db_connection)
    process_next_batch(repository, 12)

    response = client.get("/", headers={"accept": "text/html"})

    assert response.status_code == 200
    assert '<meta http-equiv="refresh" content="10">' in response.text
    assert "Current Champions" in response.text
    assert "Highest steps to 1" in response.text
    assert "Highest peak value" in response.text
    assert "Top 10 by steps to 1" in response.text
    assert "Top 10 by peak value" in response.text
    assert "Latest discoveries" in response.text
    assert "20 most recently processed" in response.text
    assert "10 most recent step records" in response.text
    assert "10 most recent peak records" in response.text
    assert "/?filter_mode=record_steps" in response.text
    assert "/?filter_mode=record_peaks" in response.text


def test_homepage_filter_mode_record_steps_limits_table_view(client):
    repository = NumberRepository(client.app.state.db_connection)
    process_next_batch(repository, 7)

    response = client.get("/?filter_mode=record_steps", headers={"accept": "text/html"})

    assert response.status_code == 200
    assert "Showing 4 matching stored numbers." in response.text
    assert "/numbers/7" in response.text
    assert "filter-link-active" in response.text
