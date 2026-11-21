import uuid
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_customer_to_order_workflow():
    email = f"workflow-{uuid.uuid4()}@example.com"

    # Register
    register_response = client.post(
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

    assert register_response.status_code in [200, 201]

    # Login
    login_response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": "Password123!",
        },
    )

    assert login_response.status_code == 200

    token = login_response.json()["access_token"]

    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Browse restaurants
    restaurants = client.get("/restaurants")

    assert restaurants.status_code == 200

    restaurant_id = restaurants.json()[0]["id"]

    # Browse menu
    menu = client.get(
        f"/restaurants/{restaurant_id}/menu"
    )

    assert menu.status_code == 200
    assert len(menu.json()["items"]) > 0

    menu_item_id = menu.json()["items"][0]["id"]

    # Add to cart
    cart_response = client.post(
        "/carts/items",
        headers=headers,
        json={
            "menu_item_id": menu_item_id,
            "quantity": 1,
        },
    )

    assert cart_response.status_code == 200

    # Verify cart exists
    cart = client.get(
        "/carts",
        headers=headers,
    )

    assert cart.status_code == 200

    # Checkout
    checkout = client.post(
        "/checkout",
        headers=headers,
    )

    assert checkout.status_code == 201

    order_id = checkout.json()["id"]

    # Retrieve order history
    orders = client.get(
        "/orders",
        headers=headers,
    )

    assert orders.status_code == 200

    returned_order_ids = {
        order["id"]
        for order in orders.json()
    }

    assert order_id in returned_order_ids