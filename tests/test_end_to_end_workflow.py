"""End-to-end API test of the full M2 workflow.
"""

from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def workflow_files(
    tmp_path: Path,
    restaurant_data_file: Path,
    menu_items_data_file: Path,
) -> dict[str, Path]:
    customers_file = tmp_path / "customers.json"
    customers_file.write_text(
        Path("data/customers.json").read_text(encoding="utf-8"), encoding="utf-8"
    )
    carts_file = tmp_path / "carts.json"
    carts_file.write_text("[]", encoding="utf-8")
    orders_file = tmp_path / "orders.json"
    orders_file.write_text("[]", encoding="utf-8")

    return {
        "restaurants": restaurant_data_file,
        "menu_items": menu_items_data_file,
        "customers": customers_file,
        "carts": carts_file,
        "orders": orders_file,
    }


def _start_app(
    client_factory: Callable[..., TestClient], files: dict[str, Path]
) -> TestClient:
    """Start the application on the given files; calling again = a restart."""
    return client_factory(
        files["restaurants"],
        files["menu_items"],
        files["customers"],
        files["carts"],
        files["orders"],
    )


def test_customer_to_order_workflow_through_api_survives_restart(
    client_factory: Callable[..., TestClient],
    workflow_files: dict[str, Path],
):
    client = _start_app(client_factory, workflow_files)

    # 1. Customer: register and sign in.
    registered = client.post(
        "/customers/register",
        json={
            "name": "Workflow Tester",
            "email": "workflow@example.com",
            "password": "Workflow123!",
        },
    )
    assert registered.status_code == 201
    customer_id = registered.json()["id"]

    login = client.post(
        "/auth/login",
        json={"email": "workflow@example.com", "password": "Workflow123!"},
    )
    assert login.status_code == 200
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}

    # 2. Restaurant/Menu: browse and pick items from the real API data.
    restaurants = client.get("/restaurants").json()
    restaurant = next(r for r in restaurants if r["name"] == "Coastal Curry")
    menu = client.get(f"/restaurants/{restaurant['id']}/menu").json()["items"]
    butter_chicken = next(i for i in menu if i["name"] == "Butter Chicken")
    naan = next(i for i in menu if i["name"] == "Garlic Naan")

    # 3. Cart: add items, change a quantity, read backend-calculated totals.
    assert client.post(
        "/carts/items",
        headers=headers,
        json={"menu_item_id": butter_chicken["id"], "quantity": 1},
    ).status_code == 200
    assert client.post(
        "/carts/items",
        headers=headers,
        json={"menu_item_id": naan["id"], "quantity": 1},
    ).status_code == 200
    cart = client.patch(
        f"/carts/items/{butter_chicken['id']}",
        headers=headers,
        json={"quantity": 2},
    )
    assert cart.status_code == 200
    cart = cart.json()

    expected_subtotal = round(butter_chicken["price"] * 2 + naan["price"], 2)
    expected_total = round(expected_subtotal + restaurant["delivery_fee"], 2)
    assert cart["subtotal"] == expected_subtotal
    assert cart["delivery_fee"] == restaurant["delivery_fee"]
    assert cart["total"] == expected_total

    # 4. Checkout: the order matches the cart and the cart is closed.
    checkout = client.post("/checkout", headers=headers)
    assert checkout.status_code == 201
    order = checkout.json()
    assert order["customer_id"] == customer_id
    assert order["restaurant_id"] == restaurant["id"]
    assert order["cart_id"] == cart["id"]
    assert order["total"] == expected_total
    assert {i["menu_item_id"]: i["quantity"] for i in order["items"]} == {
        butter_chicken["id"]: 2,
        naan["id"]: 1,
    }
    assert client.get("/carts", headers=headers).json() is None

    # 5. Order: retrievable from history and individually.
    history = client.get("/orders", headers=headers).json()
    assert [o["id"] for o in history] == [order["id"]]
    assert client.get(f"/orders/{order['id']}", headers=headers).json() == order

    # A later menu price change must not rewrite the saved order.
    assert client.patch(
        f"/restaurants/{restaurant['id']}/menu/items/{butter_chicken['id']}",
        json={"price": 99.99},
    ).status_code == 200

    # 6. Restart: a fresh application instance reading the same files.
    restarted = _start_app(client_factory, workflow_files)
    relogin = restarted.post(
        "/auth/login",
        json={"email": "workflow@example.com", "password": "Workflow123!"},
    )
    assert relogin.status_code == 200
    headers = {"Authorization": f"Bearer {relogin.json()['access_token']}"}

    saved = restarted.get(f"/orders/{order['id']}", headers=headers)
    assert saved.status_code == 200
    assert saved.json()["total"] == expected_total
    saved_chicken = next(
        i for i in saved.json()["items"] if i["menu_item_id"] == butter_chicken["id"]
    )
    assert saved_chicken["unit_price"] == butter_chicken["price"]

    # The customer can start a new cart after checkout.
    new_cart = restarted.post("/carts", headers=headers)
    assert new_cart.status_code == 201
    assert new_cart.json()["id"] != cart["id"]
