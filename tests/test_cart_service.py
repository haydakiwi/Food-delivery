
import json
from pathlib import Path

import pytest

from app.repositories.cart_repository import CartRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.menu_item_repository import MenuItemRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.services.cart_service import (
    CartCustomerNotFoundError,
    CartItemNotFoundError,
    CartMenuItemNotFoundError,
    CartMenuItemUnavailableError,
    CartNotFoundError,
    CartQuantityLimitError,
    DifferentRestaurantError,
    InactiveCartCustomerError,
    CartService,
)


@pytest.fixture
def cart_service(tmp_path: Path):
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

    customer_repo = CustomerRepository(write_json("customers.json", customers))
    restaurant_repo = RestaurantRepository(
        write_json("restaurants.json", restaurants)
    )
    menu_repo = MenuItemRepository(write_json("menu_items.json", menu_items))
    cart_repo = CartRepository(write_json("carts.json", []))

    service = CartService(
        cart_repo,
        customer_repo,
        restaurant_repo,
        menu_repo,
    )

    return service, cart_repo


def test_create_cart_for_active_customer(cart_service):
    service, _ = cart_service

    cart = service.create_cart("cust_001")

    assert cart.customer_id == "cust_001"
    assert cart.status == "active"
    assert cart.items == []
    assert cart.restaurant_id is None


def test_create_cart_rejects_unknown_customer(cart_service):
    service, _ = cart_service

    with pytest.raises(CartCustomerNotFoundError):
        service.create_cart("cust_404")


def test_inactive_customer_cannot_create_cart(cart_service):
    service, _ = cart_service

    with pytest.raises(InactiveCartCustomerError):
        service.create_cart("cust_002")


def test_get_active_cart_returns_none_when_no_cart_exists(cart_service):
    service, _ = cart_service

    assert service.get_active_cart("cust_001") is None


def test_add_item_creates_cart_automatically(cart_service):
    service, _ = cart_service

    cart = service.add_item("cust_001", "item_001", 2)

    assert cart.customer_id == "cust_001"
    assert cart.restaurant_id == "rest_001"
    assert len(cart.items) == 1
    assert cart.items[0].menu_item_id == "item_001"
    assert cart.items[0].quantity == 2


def test_add_item_increases_existing_quantity(cart_service):
    service, _ = cart_service

    service.add_item("cust_001", "item_001", 2)
    cart = service.add_item("cust_001", "item_001", 3)

    assert len(cart.items) == 1
    assert cart.items[0].quantity == 5


def test_add_item_from_same_restaurant(cart_service):
    service, _ = cart_service

    service.add_item("cust_001", "item_001", 1)
    cart = service.add_item("cust_001", "item_002", 2)

    assert len(cart.items) == 2
    assert cart.restaurant_id == "rest_001"


def test_add_item_from_different_restaurant_is_rejected(cart_service):
    service, _ = cart_service

    service.add_item("cust_001", "item_001", 1)

    with pytest.raises(DifferentRestaurantError):
        service.add_item("cust_001", "item_004", 1)


def test_unavailable_menu_item_cannot_be_added(cart_service):
    service, _ = cart_service

    with pytest.raises(CartMenuItemUnavailableError):
        service.add_item("cust_001", "item_003", 1)


def test_unknown_menu_item_cannot_be_added(cart_service):
    service, _ = cart_service

    with pytest.raises(CartMenuItemNotFoundError):
        service.add_item("cust_001", "item_404", 1)


@pytest.mark.parametrize("quantity", [0, -1, 51])
def test_add_item_rejects_invalid_quantity(cart_service, quantity):
    service, _ = cart_service

    with pytest.raises(ValueError):
        service.add_item("cust_001", "item_001", quantity)


def test_combined_quantity_cannot_exceed_50(cart_service):
    service, _ = cart_service

    service.add_item("cust_001", "item_001", 30)

    with pytest.raises(CartQuantityLimitError):
        service.add_item("cust_001", "item_001", 21)


def test_update_item_quantity(cart_service):
    service, _ = cart_service

    service.add_item("cust_001", "item_001", 2)
    cart = service.update_item_quantity("cust_001", "item_001", 4)

    assert cart.items[0].quantity == 4


def test_update_rejects_item_not_in_cart(cart_service):
    service, _ = cart_service

    service.create_cart("cust_001")

    with pytest.raises(CartItemNotFoundError):
        service.update_item_quantity("cust_001", "item_001", 2)


def test_update_rejects_unavailable_item(cart_service):
    service, _ = cart_service

    service.add_item("cust_001", "item_001", 1)

    service.menu_item_repository.update(
        "item_001",
        {"is_available": False},
    )

    with pytest.raises(CartMenuItemUnavailableError):
        service.update_item_quantity("cust_001", "item_001", 2)

def test_remove_item(cart_service):
    service, _ = cart_service

    service.add_item("cust_001", "item_001", 2)
    cart = service.remove_item("cust_001", "item_001")

    assert cart.items == []
    assert cart.restaurant_id is None


def test_remove_item_not_in_cart_is_rejected(cart_service):
    service, _ = cart_service

    service.create_cart("cust_001")

    with pytest.raises(CartItemNotFoundError):
        service.remove_item("cust_001", "item_001")


def test_clear_cart(cart_service):
    service, _ = cart_service

    service.add_item("cust_001", "item_001", 2)
    cart = service.clear_cart("cust_001")

    assert cart.items == []
    assert cart.restaurant_id is None
    assert cart.status == "active"


def test_clear_cart_without_active_cart_is_rejected(cart_service):
    service, _ = cart_service

    with pytest.raises(CartNotFoundError):
        service.clear_cart("cust_001")


def test_cart_survives_repository_restart(cart_service):
    service, cart_repo = cart_service

    created = service.add_item("cust_001", "item_001", 2)

    restarted_repo = CartRepository(cart_repo.data_path)
    saved = restarted_repo.get_active_by_customer("cust_001")

    assert saved["id"] == created.id
    assert saved["items"] == [{"menu_item_id": "item_001", "quantity": 2}]


def test_cart_total_uses_current_menu_price(cart_service):
    service, _ = cart_service

    service.add_item("cust_001", "item_001", 2)

    service.menu_item_repository.update(
        "item_001",
        {"price": 20.00},
    )

    cart = service.get_active_cart("cust_001")

    assert cart.subtotal == 40.00
    assert cart.delivery_fee == 3.99
    assert cart.total == 43.99


def test_empty_cart_has_zero_totals_after_clearing(cart_service):
    service, _ = cart_service

    service.add_item("cust_001", "item_001", 2)
    cart = service.clear_cart("cust_001")

    assert cart.items == []
    assert cart.subtotal == 0.0
    assert cart.delivery_fee == 0.0
    assert cart.total == 0.0
