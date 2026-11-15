import shutil
from pathlib import Path

import pytest

from app.repositories.cart_repository import CartRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.integrity import find_relationship_problems
from app.repositories.menu_item_repository import MenuItemRepository
from app.repositories.order_repository import OrderRepository
from app.repositories.restaurant_repository import RestaurantRepository

DATA_FILES = ["customers", "restaurants", "menu_items", "carts", "orders"]


@pytest.fixture
def data_dir(tmp_path):
    """Copy the committed seed data so the test never modifies it."""
    for name in DATA_FILES:
        shutil.copy(Path("data") / f"{name}.json", tmp_path / f"{name}.json")
    return tmp_path


def open_repositories(data_dir):
    """Build fresh repository objects; calling this again simulates a restart."""
    return {
        "customers": CustomerRepository(data_dir / "customers.json"),
        "restaurants": RestaurantRepository(data_dir / "restaurants.json"),
        "menu_items": MenuItemRepository(data_dir / "menu_items.json"),
        "carts": CartRepository(data_dir / "carts.json"),
        "orders": OrderRepository(data_dir / "orders.json"),
    }


def relationship_problems(repos):
    return find_relationship_problems(
        repos["customers"].get_all(),
        repos["restaurants"].get_all(),
        repos["menu_items"].get_all(),
        repos["carts"].get_all(),
        repos["orders"].get_all(),
    )


def test_committed_seed_data_relationships_are_valid():
    repos = open_repositories(Path("data"))
    assert relationship_problems(repos) == []


def test_customer_cart_order_workflow_survives_restart(data_dir):
    repos = open_repositories(data_dir)

    # Customer
    customer = repos["customers"].create(
        {"name": "Test Buyer", "email": "buyer@example.com", "password_hash": "hash"}
    )

    # Menu -> Cart (references only)
    menu = repos["menu_items"].get_by_restaurant("rest_004")
    cart = repos["carts"].create(customer["id"])
    repos["carts"].update(
        cart["id"],
        {
            "restaurant_id": "rest_004",
            "items": [
                {"menu_item_id": menu[0]["id"], "quantity": 2},
                {"menu_item_id": menu[1]["id"], "quantity": 1},
            ],
        },
    )

    # Cart -> Order (price snapshot from current menu data)
    saved_cart = repos["carts"].get_by_id(cart["id"])
    restaurant = repos["restaurants"].get_by_id("rest_004")
    lines = []
    for line in saved_cart["items"]:
        item = repos["menu_items"].get_by_id(line["menu_item_id"])
        lines.append(
            {
                "menu_item_id": item["id"],
                "name": item["name"],
                "unit_price": item["price"],
                "quantity": line["quantity"],
                "line_total": round(item["price"] * line["quantity"], 2),
            }
        )
    subtotal = round(sum(line["line_total"] for line in lines), 2)
    order = repos["orders"].create(
        {
            "customer_id": customer["id"],
            "restaurant_id": restaurant["id"],
            "restaurant_name": restaurant["name"],
            "cart_id": saved_cart["id"],
            "items": lines,
            "subtotal": subtotal,
            "delivery_fee": restaurant["delivery_fee"],
            "total": round(subtotal + restaurant["delivery_fee"], 2),
        }
    )
    # Close the cart only after the order is saved.
    repos["carts"].close(saved_cart["id"])

    # A later menu price change must not alter the saved order.
    original_price = lines[0]["unit_price"]
    repos["menu_items"].update(lines[0]["menu_item_id"], {"price": 99.99})

    # Restart: brand-new repository objects reading the same files.
    restarted = open_repositories(data_dir)

    assert relationship_problems(restarted) == []
    assert restarted["customers"].get_by_email("buyer@example.com")["id"] == customer["id"]
    assert restarted["carts"].get_active_by_customer(customer["id"]) is None
    assert restarted["carts"].get_by_id(cart["id"])["status"] == "checked_out"

    reloaded = restarted["orders"].get_by_customer(customer["id"])
    assert [o["id"] for o in reloaded] == [order["id"]]
    assert reloaded[0]["items"][0]["unit_price"] == original_price
    assert reloaded[0]["cart_id"] == cart["id"]

    # The customer can start a fresh cart afterwards.
    assert restarted["carts"].create(customer["id"])["status"] == "active"


def test_integrity_check_reports_broken_links():
    problems = find_relationship_problems(
        customers=[{"id": "cust_001"}],
        restaurants=[{"id": "rest_001"}, {"id": "rest_002"}],
        menu_items=[
            {"id": "item_001", "restaurant_id": "rest_001"},
            {"id": "item_002", "restaurant_id": "rest_002"},
        ],
        carts=[
            {
                "id": "cart_001",
                "customer_id": "cust_999",
                "restaurant_id": "rest_001",
                "items": [{"menu_item_id": "item_002", "quantity": 1}],
            }
        ],
        orders=[
            {
                "id": "ord_001",
                "customer_id": "cust_001",
                "restaurant_id": "rest_001",
                "cart_id": "cart_404",
                "items": [{"menu_item_id": "item_404"}],
            }
        ],
    )
    assert "Cart cart_001 references unknown customer cust_999" in problems
    assert "Cart cart_001 has item item_002 from a different restaurant" in problems
    assert "Order ord_001 references unknown cart cart_404" in problems
    assert "Order ord_001 references unknown menu item item_404" in problems