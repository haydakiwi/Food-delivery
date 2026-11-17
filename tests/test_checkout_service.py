
import json
from pathlib import Path

import pytest

from app.repositories.cart_repository import CartRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.menu_item_repository import MenuItemRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.services.cart_service import CartService
from app.services.checkout_service import (
    CheckoutCartNotFoundError,
    CheckoutMenuItemNotFoundError,
    CheckoutMenuItemUnavailableError,
    CheckoutRestaurantNotFoundError,
    EmptyCheckoutCartError,
    InactiveCheckoutCustomerError,
    CheckoutService,
)


@pytest.fixture
def checkout_service(tmp_path: Path):
    customers = [
        {
            "id": "cust_001",
            "name": "Test Customer",
            "email": "test@example.com",
            "password_hash": "test-hash",
            "role": "customer",
            "is_active": True,
            "addresses": [],
            "created_at": "2026-11-10T00:00:00+00:00",
        },
        {
            "id": "cust_002",
            "name": "Inactive Customer",
            "email": "inactive@example.com",
            "password_hash": "test-hash",
            "role": "customer",
            "is_active": False,
            "addresses": [],
            "created_at": "2026-11-10T00:00:00+00:00",
        },
    ]

    restaurants = [
        {
            "id": "rest_001",
            "name": "Coastal Curry",
            "cuisine": "Indian",
            "rating": 4.7,
            "delivery_time_minutes": 30,
            "delivery_fee": 3.99,
            "is_open": True,
            "address": "123 Main St",
        },
        {
            "id": "rest_002",
            "name": "Maple Sushi",
            "cuisine": "Japanese",
            "rating": 4.5,
            "delivery_time_minutes": 25,
            "delivery_fee": 2.99,
            "is_open": True,
            "address": "456 Maple Ave",
        },
    ]

    menu_items = [
        {
            "id": "item_001",
            "restaurant_id": "rest_001",
            "name": "Butter Chicken",
            "description": "Creamy tomato curry",
            "price": 16.99,
            "category": "Mains",
            "is_available": True,
        },
        {
            "id": "item_002",
            "restaurant_id": "rest_001",
            "name": "Garlic Naan",
            "description": "Tandoor-baked flatbread",
            "price": 3.99,
            "category": "Sides",
            "is_available": True,
        },
        {
            "id": "item_003",
            "restaurant_id": "rest_002",
            "name": "Salmon Roll",
            "description": "Salmon and avocado roll",
            "price": 11.50,
            "category": "Sushi",
            "is_available": False,
        },
        {
            "id": "item_004",
            "restaurant_id": "rest_002",
            "name": "California Roll",
            "description": "Crab and avocado roll",
            "price": 9.50,
            "category": "Sushi",
            "is_available": True,
        },
    ]

    def write_json(filename, records):
        path = tmp_path / filename
        path.write_text(json.dumps(records), encoding="utf-8")
        return path

    customer_repo = CustomerRepository(
        write_json("customers.json", customers)
    )
    restaurant_repo = RestaurantRepository(
        write_json("restaurants.json", restaurants)
    )
    menu_repo = MenuItemRepository(
        write_json("menu_items.json", menu_items)
    )
    cart_repo = CartRepository(write_json("carts.json", []))
    order_repo = OrderRepository(write_json("orders.json", []))

    cart_service = CartService(
        cart_repo,
        customer_repo,
        restaurant_repo,
        menu_repo,
    )

    service = CheckoutService(
        cart_repo,
        customer_repo,
        restaurant_repo,
        menu_repo,
        order_repo,
    )

    return (
        service,
        cart_service,
        cart_repo,
        order_repo,
        menu_repo,
        restaurant_repo,
    )


def test_checkout_creates_order_and_closes_cart(checkout_service):
    service, cart_service, cart_repo, order_repo, _, _ = checkout_service

    cart = cart_service.add_item("cust_001", "item_001", 2)
    cart_service.add_item("cust_001", "item_002", 1)

    order = service.checkout("cust_001")

    assert order.customer_id == "cust_001"
    assert order.restaurant_id == "rest_001"
    assert order.restaurant_name == "Coastal Curry"
    assert order.cart_id == cart.id
    assert order.status == "placed"

    assert len(order.items) == 2
    assert order.subtotal == 37.97
    assert order.delivery_fee == 3.99
    assert order.total == 41.96

    saved_cart = cart_repo.get_by_id(cart.id)
    assert saved_cart["status"] == "checked_out"

    saved_orders = order_repo.get_by_customer("cust_001")
    assert len(saved_orders) == 1
    assert saved_orders[0]["id"] == order.id


def test_checkout_uses_current_menu_price_and_name(checkout_service):
    service, cart_service, _, _, menu_repo, _ = checkout_service

    cart_service.add_item("cust_001", "item_001", 2)

    menu_repo.update(
        "item_001",
        {
            "name": "Updated Butter Chicken",
            "price": 19.99,
        },
    )

    order = service.checkout("cust_001")

    assert order.items[0].name == "Updated Butter Chicken"
    assert order.items[0].unit_price == 19.99
    assert order.items[0].line_total == 39.98
    assert order.subtotal == 39.98
    assert order.total == 43.97


def test_checkout_uses_current_delivery_fee(checkout_service):
    service, cart_service, _, _, _, restaurant_repo = checkout_service

    cart_service.add_item("cust_001", "item_001", 1)

    restaurant_repo.update("rest_001", {"delivery_fee": 5.50})

    order = service.checkout("cust_001")

    assert order.delivery_fee == 5.50
    assert order.total == 22.49


def test_checkout_rejects_customer_without_cart(checkout_service):
    service, *_ = checkout_service

    with pytest.raises(CheckoutCartNotFoundError):
        service.checkout("cust_001")


def test_checkout_rejects_empty_cart(checkout_service):
    service, cart_service, *_ = checkout_service

    cart_service.create_cart("cust_001")

    with pytest.raises(EmptyCheckoutCartError):
        service.checkout("cust_001")


def test_checkout_rejects_inactive_customer(checkout_service):
    service, *_ = checkout_service

    with pytest.raises(InactiveCheckoutCustomerError):
        service.checkout("cust_002")


def test_checkout_rejects_unknown_customer(checkout_service):
    service, *_ = checkout_service

    with pytest.raises(LookupError):
        service.checkout("cust_404")


def test_checkout_rejects_item_that_becomes_unavailable(checkout_service):
    service, cart_service, cart_repo, _, menu_repo, _ = checkout_service

    cart = cart_service.add_item("cust_001", "item_001", 1)

    menu_repo.update("item_001", {"is_available": False})

    with pytest.raises(CheckoutMenuItemUnavailableError):
        service.checkout("cust_001")

    assert cart_repo.get_by_id(cart.id)["status"] == "active"


def test_checkout_rejects_deleted_menu_item(checkout_service):
    service, cart_service, cart_repo, _, menu_repo, _ = checkout_service

    cart = cart_service.add_item("cust_001", "item_001", 1)

    records = menu_repo._load()
    records = [item for item in records if item["id"] != "item_001"]
    menu_repo._save(records)

    with pytest.raises(CheckoutMenuItemNotFoundError):
        service.checkout("cust_001")

    assert cart_repo.get_by_id(cart.id)["status"] == "active"


def test_checkout_rejects_deleted_restaurant(checkout_service):
    service, cart_service, cart_repo, _, _, restaurant_repo = checkout_service

    cart = cart_service.add_item("cust_001", "item_001", 1)

    restaurant_repo._save([])

    with pytest.raises(CheckoutRestaurantNotFoundError):
        service.checkout("cust_001")

    assert cart_repo.get_by_id(cart.id)["status"] == "active"


def test_failed_order_save_leaves_cart_active(checkout_service, monkeypatch):
    service, cart_service, cart_repo, order_repo, _, _ = checkout_service

    cart = cart_service.add_item("cust_001", "item_001", 1)

    def fail_order_save(order_data):
        raise OSError("Simulated order storage failure")

    monkeypatch.setattr(order_repo, "create", fail_order_save)

    with pytest.raises(OSError):
        service.checkout("cust_001")

    saved_cart = cart_repo.get_by_id(cart.id)
    assert saved_cart["status"] == "active"
    assert saved_cart["items"] == [
        {"menu_item_id": "item_001", "quantity": 1}
    ]
    assert order_repo.get_by_customer("cust_001") == []


def test_checkout_order_survives_repository_restart(checkout_service):
    service, cart_service, _, order_repo, _, _ = checkout_service

    cart_service.add_item("cust_001", "item_001", 2)
    order = service.checkout("cust_001")

    restarted_repo = OrderRepository(order_repo.data_path)
    saved_orders = restarted_repo.get_by_customer("cust_001")

    assert len(saved_orders) == 1
    assert saved_orders[0]["id"] == order.id
    assert saved_orders[0]["total"] == order.total


def test_checkout_rejects_second_checkout_of_closed_cart(checkout_service):
    service, cart_service, cart_repo, order_repo, _, _ = checkout_service

    cart = cart_service.add_item("cust_001", "item_001", 1)

    service.checkout("cust_001")

    with pytest.raises(CheckoutCartNotFoundError):
        service.checkout("cust_001")

    assert cart_repo.get_by_id(cart.id)["status"] == "checked_out"
    assert len(order_repo.get_by_customer("cust_001")) == 1
