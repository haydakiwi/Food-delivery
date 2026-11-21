import json
import uuid
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def customers_data_file(tmp_path: Path) -> Path:
    records = json.loads(
        Path("data/customers.json").read_text(encoding="utf-8")
    )

    path = tmp_path / "customers.json"
    path.write_text(
        json.dumps(records),
        encoding="utf-8",
    )

    return path


@pytest.fixture
def carts_data_file(tmp_path: Path) -> Path:
    path = tmp_path / "carts.json"

    path.write_text(
        "[]",
        encoding="utf-8",
    )

    return path


@pytest.fixture
def orders_data_file(tmp_path: Path) -> Path:
    path = tmp_path / "orders.json"

    path.write_text(
        "[]",
        encoding="utf-8",
    )

    return path


@pytest.fixture
def workflow_client(
    client_factory: Callable[..., TestClient],
    restaurant_data_file: Path,
    menu_items_data_file: Path,
    customers_data_file: Path,
    carts_data_file: Path,
    orders_data_file: Path,
) -> TestClient:
    return client_factory(
        restaurant_data_file,
        menu_items_data_file,
        customers_data_file,
        carts_data_file,
        orders_data_file,
    )


def test_customer_to_order_workflow(
    workflow_client: TestClient,
):
    email = f"workflow-{uuid.uuid4()}@example.com"

    registration = workflow_client.post(
        "/customers/register",
        json={
            "name": "Workflow Test",
            "email": email,
            "password": "Password123!",
            "phone": "2505551234",
            "addresses": [
                {
                    "label": "Home",
                    "street": "123 Test St",
                    "city": "Kelowna",
                    "province": "BC",
                    "postal_code": "V1V1V1",
                    "is_default": True,
                }
            ],
        },
    )

    assert registration.status_code == 201

    login = workflow_client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "Password123!",
        },
    )

    assert login.status_code == 200

    token = login.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}",
    }

    restaurants = workflow_client.get(
        "/restaurants"
    )

    assert restaurants.status_code == 200
    assert restaurants.json()

    restaurant_id = restaurants.json()[0]["id"]

    menu = workflow_client.get(
        f"/restaurants/{restaurant_id}/menu"
    )

    assert menu.status_code == 200
    assert menu.json()["items"]

    menu_item = menu.json()["items"][0]
    expected_item_id = menu_item["id"]

    add_to_cart = workflow_client.post(
        "/carts/items",
        headers=headers,
        json={
            "menu_item_id": menu_item["id"],
            "quantity": 1,
        },
    )

    assert add_to_cart.status_code == 200

    cart_before_checkout = workflow_client.get(
        "/carts",
        headers=headers,
    )

    assert cart_before_checkout.status_code == 200

    cart_data = cart_before_checkout.json()

    assert cart_data["items"]
    assert len(cart_data["items"]) == 1

    expected_total = cart_data["total"]
    customer_id = registration.json()["id"]

    checkout = workflow_client.post(
        "/checkout",
        headers=headers,
    )

    assert checkout.status_code == 201

    order = checkout.json()

    assert order["id"]
    assert order["items"]
    assert order["total"] > 0

    assert order["customer_id"] == customer_id
    assert order["total"] == expected_total

    orders = workflow_client.get(
        "/orders",
        headers=headers,
    )

    assert orders.status_code == 200

    order_ids = {
        record["id"]
        for record in orders.json()
    }

    assert order["id"] in order_ids

    matching_order = next(
        record
        for record in orders.json()
        if record["id"] == order["id"]
    )

    assert matching_order["items"]
    assert matching_order["total"] == order["total"]

    first_item = matching_order["items"][0]

    assert first_item["menu_item_id"] == expected_item_id
    assert first_item["quantity"] == 1

    cart_after_checkout = workflow_client.get(
        "/carts",
        headers=headers,
    )

    assert cart_after_checkout.status_code == 200

    final_cart = cart_after_checkout.json()

    assert final_cart is None