"""End-to-end tests for the restaurant-list endpoint."""

from collections.abc import Callable
import json
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
    required_fields = {
        "id",
        "name",
        "cuisine",
        "rating",
        "delivery_time_minutes",
        "delivery_fee",
        "is_open",
        "address",
    }
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


def test_create_restaurant_returns_201(client) -> None:
    response = client.post(
        "/restaurants",
        json={
            "name": "Pizza Place",
            "cuisine": "Italian",
            "rating": 4.5,
            "delivery_time_minutes": 30,
            "delivery_fee": 2.99,
            "is_open": True,
            "address": "789 Test Road",
        },
    )

    assert response.status_code == 201

    restaurant = response.json()
    assert restaurant["name"] == "Pizza Place"
    assert restaurant["cuisine"] == "Italian"
    assert restaurant["id"].startswith("rest_")


def test_create_restaurant_rejects_duplicate_name(client) -> None:
    response = client.post(
        "/restaurants",
        json={
            "name": "  MAPLE SUSHI  ",
            "cuisine": "Japanese",
            "rating": 4.5,
            "delivery_time_minutes": 30,
            "delivery_fee": 2.99,
            "is_open": True,
            "address": "789 Test Road",
        },
    )

    assert response.status_code == 400


def test_create_restaurant_rejects_invalid_data(client) -> None:
    response = client.post(
        "/restaurants",
        json={
            "name": "Invalid Restaurant",
            "cuisine": "Italian",
            "rating": 7.0,
            "delivery_time_minutes": 0,
            "delivery_fee": -1.0,
            "is_open": True,
            "address": "789 Test Road",
        },
    )

    assert response.status_code == 422


def test_update_restaurant(client) -> None:
    response = client.patch(
        "/restaurants/1",
        json={
            "delivery_fee": 5.99,
            "is_open": False,
        },
    )

    assert response.status_code == 200

    restaurant = response.json()
    assert restaurant["delivery_fee"] == 5.99
    assert restaurant["is_open"] is False


def test_update_unknown_restaurant_returns_404(client) -> None:
    response = client.patch(
        "/restaurants/rest_404",
        json={"name": "Ghost Restaurant"},
    )

    assert response.status_code == 404


def test_create_menu_item_returns_201(client) -> None:
    response = client.post(
        "/restaurants/1/menu/items",
        json={
            "name": "Miso Soup",
            "description": "Traditional soup",
            "price": 4.99,
            "category": "Sides",
            "is_available": True,
        },
    )

    assert response.status_code == 201

    item = response.json()
    assert item["name"] == "Miso Soup"
    assert item["restaurant_id"] == "1"
    assert item["id"].startswith("item_")


def test_create_menu_item_for_unknown_restaurant_returns_404(client) -> None:
    response = client.post(
        "/restaurants/rest_404/menu/items",
        json={
            "name": "Ghost Item",
            "description": "",
            "price": 5.99,
            "category": "Mains",
            "is_available": True,
        },
    )

    assert response.status_code == 404


def test_create_menu_item_rejects_invalid_data(client) -> None:
    response = client.post(
        "/restaurants/1/menu/items",
        json={
            "name": "Invalid Item",
            "description": "",
            "price": -5.00,
            "category": "Sides",
            "is_available": True,
        },
    )

    assert response.status_code == 422


def test_update_menu_item(client) -> None:
    response = client.patch(
        "/restaurants/1/menu/items/item_001",
        json={
            "price": 14.99,
            "is_available": False,
        },
    )

    assert response.status_code == 200

    item = response.json()
    assert item["price"] == 14.99
    assert item["is_available"] is False


def test_update_menu_item_through_wrong_restaurant_returns_404(client) -> None:
    response = client.patch(
        "/restaurants/1/menu/items/item_003",
        json={"price": 15.99},
    )

    assert response.status_code == 404


def test_created_restaurant_persists_to_json(
    client,
    restaurant_data_file: Path,
) -> None:
    response = client.post(
        "/restaurants",
        json={
            "name": "Persistent Pizza",
            "cuisine": "Italian",
            "rating": 4.6,
            "delivery_time_minutes": 25,
            "delivery_fee": 3.49,
            "is_open": True,
            "address": "100 Persistence Ave",
        },
    )

    assert response.status_code == 201
    created = response.json()

    saved_data = json.loads(
        restaurant_data_file.read_text(encoding="utf-8")
    )

    assert any(
        restaurant["id"] == created["id"]
        and restaurant["name"] == "Persistent Pizza"
        for restaurant in saved_data
    )


def test_updated_menu_item_persists_to_json(
    client,
    menu_items_data_file: Path,
) -> None:
    response = client.patch(
        "/restaurants/1/menu/items/item_001",
        json={
            "price": 19.99,
            "is_available": False,
        },
    )

    assert response.status_code == 200

    saved_data = json.loads(
        menu_items_data_file.read_text(encoding="utf-8")
    )

    saved_item = next(
        item for item in saved_data if item["id"] == "item_001"
    )

    assert saved_item["price"] == 19.99
    assert saved_item["is_available"] is False


def test_openapi_documents_management_endpoints(client) -> None:
    response = client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert "post" in paths["/restaurants"]
    assert "patch" in paths["/restaurants/{restaurant_id}"]
    assert "post" in paths["/restaurants/{restaurant_id}/menu/items"]
    assert (
        "patch"
        in paths[
            "/restaurants/{restaurant_id}/menu/items/{item_id}"
        ]
    )

    assert (
        paths["/restaurants"]["post"]["responses"]["201"]["description"]
        == "Successful Response"
    )

    assert "400" in paths["/restaurants"]["post"]["responses"]
    assert "422" in paths["/restaurants"]["post"]["responses"]

    assert (
        "404"
        in paths["/restaurants/{restaurant_id}"]["patch"]["responses"]
    )