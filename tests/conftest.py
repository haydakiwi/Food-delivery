"""Shared pytest fixtures for API tests.

The application is imported only after the test data path is configured.  This
keeps tests isolated from ``data/restaurants.json`` and lets each failure test
start the app with its own data source.
"""

from __future__ import annotations

import importlib
import json
import sys
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def sample_restaurants() -> list[dict[str, object]]:
    """Restaurant records that match the fields agreed on by the team."""

    return [
        {
            "id": 1,
            "name": "Coastal Curry",
            "cuisine": "Indian",
            "rating": 4.7,
            "delivery_time": 30,
        },
        {
            "id": 2,
            "name": "Maple Sushi",
            "cuisine": "Japanese",
            "rating": 4.5,
            "delivery_time": 25,
        },
    ]


@pytest.fixture
def restaurant_data_file(
    tmp_path: Path, sample_restaurants: list[dict[str, object]]
) -> Path:
    """Write valid restaurant data outside the committed data directory."""

    data_file = tmp_path / "restaurants.json"
    data_file.write_text(json.dumps(sample_restaurants), encoding="utf-8")
    return data_file


@pytest.fixture
def invalid_restaurant_data_file(tmp_path: Path) -> Path:
    """Create a file whose contents are deliberately not valid JSON."""

    data_file = tmp_path / "invalid-restaurants.json"
    data_file.write_text("{not valid json", encoding="utf-8")
    return data_file


@pytest.fixture
def missing_restaurant_data_file(tmp_path: Path) -> Path:
    """Return a path that is guaranteed not to exist."""

    return tmp_path / "missing-restaurants.json"


def _clear_application_modules() -> None:
    """Remove cached modules that may have captured an older data path."""

    reload_prefixes = (
        "app.api",
        "app.core.config",
        "app.main",
        "app.repositories",
        "app.services",
    )
    for module_name in list(sys.modules):
        if module_name.startswith(reload_prefixes):
            sys.modules.pop(module_name, None)


@pytest.fixture
def client_factory(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[Callable[[Path], TestClient]]:
    """Build a test client configured to read from a chosen data file."""

    clients: list[TestClient] = []

    def build_client(data_path: Path) -> TestClient:
        monkeypatch.setenv("DATA_PATH", str(data_path))
        _clear_application_modules()

        # This fallback supports the current config module while Part A changes
        # it to read DATA_PATH from the environment as required by the brief.
        config = importlib.import_module("app.core.config")
        monkeypatch.setattr(config, "DATA_PATH", str(data_path), raising=False)

        application = importlib.import_module("app.main").app
        client = TestClient(application, raise_server_exceptions=False)
        clients.append(client)
        return client

    yield build_client

    for client in clients:
        client.close()


@pytest.fixture
def client(
    client_factory: Callable[[Path], TestClient], restaurant_data_file: Path
) -> TestClient:
    """Return a client backed by valid temporary restaurant data."""

    return client_factory(restaurant_data_file)
