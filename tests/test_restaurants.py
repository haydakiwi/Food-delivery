"""End-to-end tests for the restaurant-list endpoint."""

from collections.abc import Callable
from pathlib import Path

from fastapi.testclient import TestClient


def test_restaurants_returns_temporary_data(
    client: TestClient, sample_restaurants: list[dict[str, object]]
) -> None:
    response = client.get("/restaurants")

    assert response.status_code == 200
    assert response.json() == sample_restaurants


def test_restaurants_match_the_agreed_schema(client: TestClient) -> None:
    response = client.get("/restaurants")

    assert response.status_code == 200
    required_fields = {"id", "name", "cuisine", "rating", "delivery_time"}
    assert response.json(), "The restaurant list must not be empty"
    assert all(required_fields <= restaurant.keys() for restaurant in response.json())


def test_restaurants_handles_a_missing_data_file(
    client_factory: Callable[[Path], TestClient], missing_restaurant_data_file: Path
) -> None:
    response = client_factory(missing_restaurant_data_file).get("/restaurants")

    assert response.status_code in {500, 503}


def test_restaurants_handles_invalid_json(
    client_factory: Callable[[Path], TestClient], invalid_restaurant_data_file: Path
) -> None:
    response = client_factory(invalid_restaurant_data_file).get("/restaurants")

    assert response.status_code in {500, 503}
