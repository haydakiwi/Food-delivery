import json
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def checkout_api_files(tmp_path: Path) -> dict[str, Path]:
    customers_file = tmp_path / "customers.json"
    customers_file.write_text(
        Path("data/customers.json").read_text(encoding="utf-8"),
        encoding="utf-8",
    )

    carts_file = tmp_path / "carts.json"
    carts_file.write_text("[]", encoding="utf-8")

    orders_file = tmp_path / "orders.json"
    orders_file.write_text("[]", encoding="utf-8")

    return {
        "customers": customers_file,
        "carts": carts_file,
        "orders": orders_file,
    }


@pytest.fixture
def checkout_api_client(
    client_factory: Callable[..., TestClient],
    restaurant_data_file: Path,
    menu_items_data_file: Path,
    checkout_api_files: dict[str, Path],
) -> TestClient:
    return client_factory(
        restaurant_data_file,
        menu_items_data_file,
        checkout_api_files["customers"],
        checkout_api_files["carts"],
        checkout_api_files["orders"],
    )


def _login(
    client: TestClient,
    email: str = "alice@example.com",
    password: str = "Password123!",
) -> str:
    response = client.post(
        "/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _headers(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def _add_item(
    client: TestClient,
    headers: dict[str, str],
    menu_item_id: str = "item_001",
    quantity: int = 1,
):
    return client.post(
        "/carts/items",
        headers=headers,
        json={"menu_item_id": menu_item_id, "quantity": quantity},
    )


def test_checkout_requires_authentication(checkout_api_client: TestClient):
    response = checkout_api_client.post("/checkout")
    assert response.status_code == 401


def test_admin_cannot_checkout(checkout_api_client: TestClient):
    token = _login(checkout_api_client, "admin@example.com")
    response = checkout_api_client.post(
        "/checkout",
        headers=_headers(token),
    )
    assert response.status_code == 403


def test_checkout_without_cart_returns_404(checkout_api_client: TestClient):
    token = _login(checkout_api_client)
    response = checkout_api_client.post(
        "/checkout",
        headers=_headers(token),
    )
    assert response.status_code == 404


def test_checkout_rejects_empty_cart(checkout_api_client: TestClient):
    token = _login(checkout_api_client)
    headers = _headers(token)

    create_cart = checkout_api_client.post("/carts", headers=headers)
    response = checkout_api_client.post("/checkout", headers=headers)

    assert create_cart.status_code == 201
    assert response.status_code == 409


def test_customer_can_checkout_and_cart_is_closed(
    checkout_api_client: TestClient,
):
    token = _login(checkout_api_client)
    headers = _headers(token)

    _add_item(checkout_api_client, headers, "item_001", 2)
    _add_item(checkout_api_client, headers, "item_002", 1)

    response = checkout_api_client.post("/checkout", headers=headers)

    assert response.status_code == 201
    order = response.json()

    assert order["customer_id"] == "cust_001"
    assert order["restaurant_id"] == "1"
    assert order["status"] == "placed"
    assert len(order["items"]) == 2
    assert order["subtotal"] == 37.97
    assert order["delivery_fee"] == 3.99
    assert order["total"] == 41.96

    cart_response = checkout_api_client.get("/carts", headers=headers)
    assert cart_response.status_code == 200
    assert cart_response.json() is None


def test_checkout_uses_current_menu_price(
    checkout_api_client: TestClient,
    menu_items_data_file: Path,
):
    token = _login(checkout_api_client)
    headers = _headers(token)

    _add_item(checkout_api_client, headers, "item_001", 2)

    menu_items = json.loads(
        menu_items_data_file.read_text(encoding="utf-8")
    )
    menu_item = next(
        item for item in menu_items if item["id"] == "item_001"
    )
    menu_item["price"] = 20.00
    menu_items_data_file.write_text(
        json.dumps(menu_items),
        encoding="utf-8",
    )

    response = checkout_api_client.post("/checkout", headers=headers)

    assert response.status_code == 201
    assert response.json()["items"][0]["unit_price"] == 20.00
    assert response.json()["subtotal"] == 40.00
    assert response.json()["total"] == 43.99


def test_checkout_rejects_item_that_became_unavailable(
    checkout_api_client: TestClient,
    menu_items_data_file: Path,
):
    token = _login(checkout_api_client)
    headers = _headers(token)

    _add_item(checkout_api_client, headers, "item_001", 1)

    menu_items = json.loads(
        menu_items_data_file.read_text(encoding="utf-8")
    )
    menu_item = next(
        item for item in menu_items if item["id"] == "item_001"
    )
    menu_item["is_available"] = False
    menu_items_data_file.write_text(
        json.dumps(menu_items),
        encoding="utf-8",
    )

    response = checkout_api_client.post("/checkout", headers=headers)

    assert response.status_code == 409

    cart_response = checkout_api_client.get("/carts", headers=headers)
    assert cart_response.status_code == 200
    assert cart_response.json() is not None
    assert cart_response.json()["status"] == "active"


def test_checkout_creates_order_for_authenticated_customer(
    checkout_api_client: TestClient,
):
    token = _login(checkout_api_client)
    headers = _headers(token)

    _add_item(checkout_api_client, headers)

    response = checkout_api_client.post("/checkout", headers=headers)

    assert response.status_code == 201
    assert response.json()["customer_id"] == "cust_001"
    assert response.json()["id"].startswith("ord_")
