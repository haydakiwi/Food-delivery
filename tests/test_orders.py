"""API tests for retrieving orders (GET /orders and GET /orders/{order_id})."""

from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def orders_api_client(
    tmp_path: Path,
    client_factory: Callable[..., TestClient],
    restaurant_data_file: Path,
    menu_items_data_file: Path,
) -> TestClient:
    """Client on temporary copies of every data file; committed data is untouched."""
    customers_file = tmp_path / "customers.json"
    customers_file.write_text(
        Path("data/customers.json").read_text(encoding="utf-8"), encoding="utf-8"
    )
    carts_file = tmp_path / "carts.json"
    carts_file.write_text("[]", encoding="utf-8")
    orders_file = tmp_path / "orders.json"
    orders_file.write_text("[]", encoding="utf-8")

    return client_factory(
        restaurant_data_file,
        menu_items_data_file,
        customers_file,
        carts_file,
        orders_file,
    )


def _login(client: TestClient, email: str = "alice@example.com") -> dict[str, str]:
    response = client.post(
        "/auth/login", json={"email": email, "password": "Password123!"}
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def _place_order(client: TestClient, headers: dict[str, str]) -> dict:
    added = client.post(
        "/carts/items",
        headers=headers,
        json={"menu_item_id": "item_001", "quantity": 2},
    )
    assert added.status_code == 200
    response = client.post("/checkout", headers=headers)
    assert response.status_code == 201
    return response.json()


def test_customer_can_get_own_order_by_id(orders_api_client: TestClient):
    headers = _login(orders_api_client)
    order = _place_order(orders_api_client, headers)

    response = orders_api_client.get(f"/orders/{order['id']}", headers=headers)

    assert response.status_code == 200
    assert response.json() == order


def test_get_order_by_id_matches_order_history(orders_api_client: TestClient):
    headers = _login(orders_api_client)
    order = _place_order(orders_api_client, headers)

    history = orders_api_client.get("/orders", headers=headers).json()
    single = orders_api_client.get(f"/orders/{order['id']}", headers=headers).json()

    assert [o["id"] for o in history] == [order["id"]]
    assert single == history[0]


def test_unknown_order_returns_404(orders_api_client: TestClient):
    headers = _login(orders_api_client)

    response = orders_api_client.get("/orders/ord_999", headers=headers)

    assert response.status_code == 404


def test_customer_cannot_see_another_customers_order(orders_api_client: TestClient):
    alice = _login(orders_api_client, "alice@example.com")
    order = _place_order(orders_api_client, alice)

    ben = _login(orders_api_client, "ben@example.com")
    response = orders_api_client.get(f"/orders/{order['id']}", headers=ben)

    # 404, not 403: another customer must not learn that the order exists.
    assert response.status_code == 404
    assert orders_api_client.get("/orders", headers=ben).json() == []


def test_get_order_requires_authentication(orders_api_client: TestClient):
    response = orders_api_client.get("/orders/ord_001")

    assert response.status_code == 401


def test_admin_cannot_use_customer_order_endpoint(orders_api_client: TestClient):
    admin = _login(orders_api_client, "admin@example.com")

    response = orders_api_client.get("/orders/ord_001", headers=admin)

    assert response.status_code == 403


def test_openapi_documents_get_order_endpoint(orders_api_client: TestClient):
    paths = orders_api_client.get("/openapi.json").json()["paths"]

    assert "get" in paths["/orders/{order_id}"]
    assert "404" in paths["/orders/{order_id}"]["get"]["responses"]