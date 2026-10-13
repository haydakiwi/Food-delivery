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


def test_restaurants_searches_names_case_insensitively(client: TestClient) -> None:
    response = client.get("/restaurants", params={"search": "COASTAL"})

    assert response.status_code == 200
    assert [restaurant["id"] for restaurant in response.json()] == ["1"]


def test_restaurants_filters_by_cuisine_and_open_status(client: TestClient) -> None:
    response = client.get(
        "/restaurants", params={"cuisine": "japanese", "is_open": True}
    )

    assert response.status_code == 200
    assert [restaurant["id"] for restaurant in response.json()] == ["2"]


def test_restaurant_details_returns_one_restaurant(client: TestClient) -> None:
    response = client.get("/restaurants/2")

    assert response.status_code == 200
    assert response.json()["name"] == "Maple Sushi"


def test_restaurant_details_returns_404_for_unknown_id(client: TestClient) -> None:
    response = client.get("/restaurants/404")

    assert response.status_code == 404
    assert response.json() == {"detail": "Restaurant '404' not found"}


def test_restaurant_menu_returns_linked_items(client: TestClient) -> None:
    response = client.get("/restaurants/1/menu")

    assert response.status_code == 200
    assert response.json()["restaurant_id"] == "1"
    assert [item["id"] for item in response.json()["items"]] == [
        "item_001",
        "item_002",
    ]


def test_restaurant_menu_returns_404_for_unknown_restaurant(
    client: TestClient,
) -> None:
    response = client.get("/restaurants/404/menu")

    assert response.status_code == 404


def test_menu_item_details_returns_one_item(client: TestClient) -> None:
    response = client.get("/restaurants/1/menu/items/item_001")

    assert response.status_code == 200
    assert response.json()["name"] == "Butter Chicken"


def test_menu_item_returns_404_for_unknown_item(client: TestClient) -> None:
    response = client.get("/restaurants/1/menu/items/item_404")

    assert response.status_code == 404


def test_menu_item_from_another_restaurant_is_not_exposed(
    client: TestClient,
) -> None:
    response = client.get("/restaurants/1/menu/items/item_003")

    assert response.status_code == 404


def test_openapi_documents_customer_endpoints(client: TestClient) -> None:
    schema = client.get("/openapi.json").json()

    list_operation = schema["paths"]["/restaurants"]["get"]
    assert {parameter["name"] for parameter in list_operation["parameters"]} == {
        "search",
        "cuisine",
        "is_open",
    }
    assert "200" in list_operation["responses"]
    assert "404" in schema["paths"]["/restaurants/{restaurant_id}"]["get"][
        "responses"
    ]


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
