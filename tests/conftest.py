import os
import time
import uuid
from collections.abc import Iterator

import httpx
import psycopg
import pytest
from psycopg.rows import dict_row

API_URL = os.environ.get("API_URL", "http://localhost:8010")
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgres@localhost:5433/bikeshare")


@pytest.fixture(scope="session")
def api() -> Iterator[httpx.Client]:
    with httpx.Client(base_url=API_URL, timeout=10) as client:
        _wait_until_healthy(client)
        yield client


@pytest.fixture(scope="session")
def db() -> Iterator[psycopg.Connection]:
    # Autocommit keeps every query on fresh data, so rows written through the API are visible.
    with psycopg.connect(DATABASE_URL, row_factory=dict_row, autocommit=True) as connection:
        yield connection


@pytest.fixture
def unique_name() -> str:
    return f"Test station {uuid.uuid4().hex[:8]}"


@pytest.fixture
def created_station_ids(api: httpx.Client) -> Iterator[list[int]]:
    """Collects ids of stations a test creates and removes them afterwards."""
    ids: list[int] = []
    yield ids
    for station_id in ids:
        api.delete(f"/stations/{station_id}")


def _wait_until_healthy(client: httpx.Client, attempts: int = 30) -> None:
    for _ in range(attempts):
        try:
            if client.get("/health").status_code == 200:
                return
        except httpx.TransportError:
            pass
        time.sleep(1)
    pytest.exit(f"API at {API_URL} is not healthy. Start it with: docker compose up -d --build")
