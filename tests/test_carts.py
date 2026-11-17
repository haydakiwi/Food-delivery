
import json
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def cart_api_client(
    client_factory: Callable[..., TestClient],
    restaurant_data_file: Path,
    menu_items_data_file: Path,
    tmp_path: Path,
) -> TestClient:
    customers_file = tmp_path / "customers.json"
    customers_file.write_text(
        Path("data/customers.json").read_text(encoding="utf-8"),
        encoding="utf-8",
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


def test_get_cart_requires_authentication(cart_api_client: TestClient):
    response = cart_api_client.get("/carts")
    assert response.status_code == 401


def test_get_cart_returns_null_when_no_active_cart_exists(
    cart_api_client: TestClient,
):
    token = _login(cart_api_client)
    response = cart_api_client.get("/carts", headers=_headers(token))

    assert response.status_code == 200
    assert response.json() is None


def test_customer_can_create_cart(cart_api_client: TestClient):
    token = _login(cart_api_client)
    response = cart_api_client.post("/carts", headers=_headers(token))

    assert response.status_code == 201
    assert response.json()["customer_id"] == "cust_001"
    assert response.json()["status"] == "active"
    assert response.json()["items"] == []


def test_customer_cannot_create_second_active_cart(
    cart_api_client: TestClient,
):
    token = _login(cart_api_client)
    headers = _headers(token)

    first = cart_api_client.post("/carts", headers=headers)
    second = cart_api_client.post("/carts", headers=headers)

    assert first.status_code == 201
    assert second.status_code == 409


def test_customer_can_get_own_active_cart(cart_api_client: TestClient):
    token = _login(cart_api_client)
    headers = _headers(token)

    cart_api_client.post("/carts", headers=headers)
    response = cart_api_client.get("/carts", headers=headers)

    assert response.status_code == 200
    assert response.json()["customer_id"] == "cust_001"


def test_customer_can_add_item_and_cart_is_created_automatically(
    cart_api_client: TestClient,
):
    token = _login(cart_api_client)
    response = cart_api_client.post(
        "/carts/items",
        headers=_headers(token),
        json={"menu_item_id": "item_001", "quantity": 2},
    )

    assert response.status_code == 200
    assert response.json()["customer_id"] == "cust_001"
    assert response.json()["items"] == [
        {"menu_item_id": "item_001", "quantity": 2}
    ]


def test_adding_existing_item_increments_quantity(
    cart_api_client: TestClient,
):
    token = _login(cart_api_client)
    headers = _headers(token)

    cart_api_client.post(
        "/carts/items",
        headers=headers,
        json={"menu_item_id": "item_001", "quantity": 2},
    )
    response = cart_api_client.post(
        "/carts/items",
        headers=headers,
        json={"menu_item_id": "item_001", "quantity": 3},
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["quantity"] == 5


def test_customer_cannot_add_item_from_different_restaurant(
    cart_api_client: TestClient,
):
    token = _login(cart_api_client)
    headers = _headers(token)

    cart_api_client.post(
        "/carts/items",
        headers=headers,
        json={"menu_item_id": "item_001", "quantity": 1},
    )
    response = cart_api_client.post(
        "/carts/items",
        headers=headers,
        json={"menu_item_id": "item_003", "quantity": 1},
    )

    assert response.status_code == 409


def test_customer_cannot_add_unavailable_menu_item(
    cart_api_client: TestClient,
):
    token = _login(cart_api_client)
    response = cart_api_client.post(
        "/carts/items",
        headers=_headers(token),
        json={"menu_item_id": "item_003", "quantity": 1},
    )

    assert response.status_code == 409


def test_adding_unknown_menu_item_returns_404(
    cart_api_client: TestClient,
):
    token = _login(cart_api_client)
    response = cart_api_client.post(
        "/carts/items",
        headers=_headers(token),
        json={"menu_item_id": "item_999", "quantity": 1},
    )

    assert response.status_code == 404


@pytest.mark.parametrize("quantity", [0, -1, 51])
def test_add_item_rejects_invalid_quantity(
    cart_api_client: TestClient,
    quantity: int,
):
    token = _login(cart_api_client)
    response = cart_api_client.post(
        "/carts/items",
        headers=_headers(token),
        json={"menu_item_id": "item_001", "quantity": quantity},
    )

    assert response.status_code == 422


def test_customer_can_update_item_quantity(cart_api_client: TestClient):
    token = _login(cart_api_client)
    headers = _headers(token)

    cart_api_client.post(
        "/carts/items",
        headers=headers,
        json={"menu_item_id": "item_001", "quantity": 2},
    )
    response = cart_api_client.patch(
        "/carts/items/item_001",
        headers=headers,
        json={"quantity": 4},
    )

    assert response.status_code == 200
    assert response.json()["items"][0]["quantity"] == 4


def test_updating_missing_cart_item_returns_404(
    cart_api_client: TestClient,
):
    token = _login(cart_api_client)
    response = cart_api_client.patch(
        "/carts/items/item_001",
        headers=_headers(token),
        json={"quantity": 4},
    )

    assert response.status_code == 404


def test_customer_can_remove_cart_item(cart_api_client: TestClient):
    token = _login(cart_api_client)
    headers = _headers(token)

    cart_api_client.post(
        "/carts/items",
        headers=headers,
        json={"menu_item_id": "item_001", "quantity": 2},
    )
    response = cart_api_client.delete(
        "/carts/items/item_001",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["restaurant_id"] is None


def test_customer_can_clear_cart(cart_api_client: TestClient):
    token = _login(cart_api_client)
    headers = _headers(token)

    cart_api_client.post(
        "/carts/items",
        headers=headers,
        json={"menu_item_id": "item_001", "quantity": 2},
    )
    cart_api_client.post(
        "/carts/items",
        headers=headers,
        json={"menu_item_id": "item_002", "quantity": 1},
    )
    response = cart_api_client.delete("/carts/items", headers=headers)

    assert response.status_code == 200
    assert response.json()["items"] == []
    assert response.json()["restaurant_id"] is None


def test_customer_cannot_access_another_customers_cart(
    cart_api_client: TestClient,
):
    alice_token = _login(cart_api_client)
    ben_token = _login(cart_api_client, "ben@example.com")

    alice_headers = _headers(alice_token)
    ben_headers = _headers(ben_token)

    cart_api_client.post(
        "/carts/items",
        headers=alice_headers,
        json={"menu_item_id": "item_001", "quantity": 1},
    )

    ben_cart = cart_api_client.get("/carts", headers=ben_headers)

    assert ben_cart.status_code == 200
    assert ben_cart.json() is None


def test_cart_endpoints_reject_admin_role(cart_api_client: TestClient):
    admin_token = _login(cart_api_client, "admin@example.com")
    response = cart_api_client.get(
        "/carts",
        headers=_headers(admin_token),
    )

    assert response.status_code == 403



def test_inactive_customer_cannot_access_cart(
    cart_api_client: TestClient,
    tmp_path: Path,
):
    customers_file = tmp_path / "customers.json"
    customers = json.loads(customers_file.read_text(encoding="utf-8"))

    carla = next(
        customer for customer in customers
        if customer["email"] == "carla@example.com"
    )
    carla["is_active"] = True
    customers_file.write_text(json.dumps(customers), encoding="utf-8")

    inactive_token = _login(cart_api_client, "carla@example.com")
    headers = _headers(inactive_token)

    deactivation = cart_api_client.post(
        "/customers/me/deactivate",
        headers=headers,
    )
    response = cart_api_client.get("/carts", headers=headers)

    assert deactivation.status_code == 200
    assert response.status_code == 403


def test_cart_changes_persist_to_json_file(
    cart_api_client: TestClient,
    tmp_path: Path,
):
    token = _login(cart_api_client)
    headers = _headers(token)

    cart_api_client.post(
        "/carts/items",
        headers=headers,
        json={"menu_item_id": "item_001", "quantity": 2},
    )

    carts_file = tmp_path / "carts.json"
    saved_carts = json.loads(carts_file.read_text(encoding="utf-8"))

    assert len(saved_carts) == 1
    assert saved_carts[0]["customer_id"] == "cust_001"
    assert saved_carts[0]["items"][0]["quantity"] == 2


def test_openapi_documents_cart_endpoints(cart_api_client: TestClient):
    schema = cart_api_client.get("/openapi.json").json()

    assert "/carts" in schema["paths"]
    assert "/carts/items" in schema["paths"]
    assert "/carts/items/{menu_item_id}" in schema["paths"]
