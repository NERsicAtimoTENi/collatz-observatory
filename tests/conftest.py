import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client(tmp_path):
    db_path = tmp_path / "test_collatz.db"
    app = create_app(db_path=db_path, seed_data=False)

    with TestClient(app) as test_client:
        yield test_client
