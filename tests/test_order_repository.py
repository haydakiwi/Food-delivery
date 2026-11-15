import json

import pytest

from app.repositories.order_repository import (
    InvalidOrderError,
    OrderDataError,
    OrderRepository,
)

ORDER_INPUT = {
    "customer_id": "cust_001",
    "restaurant_id": "rest_001",
    "restaurant_name": "Sakura Sushi House",
    "cart_id": "cart_001",
    "items": [
        {"menu_item_id": "item_001", "name": "Salmon Nigiri", "unit_price": 6.50, "quantity": 2, "line_total": 13.00},
        {"menu_item_id": "item_002", "name": "Miso Soup", "unit_price": 3.50, "quantity": 1, "line_total": 3.50},
    ],
    "subtotal": 16.50,
    "delivery_fee": 2.99,
    "total": 19.49,
}

EXISTING_ORDER = {
    **ORDER_INPUT,
    "id": "ord_001",
    "customer_id": "cust_002",
    "status": "placed",
    "created_at": "2026-11-09T00:00:00+00:00",
    "delivery_address": None,
}


@pytest.fixture
def order_file(tmp_path):
    """Temporary orders.json so committed data is never touched."""
    path = tmp_path / "orders.json"
    path.write_text(json.dumps([EXISTING_ORDER]), encoding="utf-8")
    return path


# Creating


def test_create_assigns_id_status_and_timestamp(order_file):
    order = OrderRepository(order_file).create(ORDER_INPUT)
    assert order["id"] == "ord_002"
    assert order["status"] == "placed"
    assert order["created_at"]
    assert order["total"] == 19.49


def test_create_ignores_id_sent_by_caller(order_file):
    order = OrderRepository(order_file).create({**ORDER_INPUT, "id": "ord_001"})
    assert order["id"] == "ord_002"


def test_created_order_survives_restart(order_file):
    OrderRepository(order_file).create(ORDER_INPUT)
    restarted = OrderRepository(order_file)
    saved = restarted.get_by_id("ord_002")
    assert saved["items"][0]["unit_price"] == 6.50
    assert saved["cart_id"] == "cart_001"


def test_create_never_reuses_an_id(tmp_path):
    path = tmp_path / "orders.json"
    path.write_text(json.dumps([{**EXISTING_ORDER, "id": "ord_007"}]), encoding="utf-8")
    assert OrderRepository(path).create(ORDER_INPUT)["id"] == "ord_008"


@pytest.mark.parametrize(
    "bad_change",
    [
        {"total": 99.99},  # total doesn't match subtotal + fee
        {"subtotal": 1.00, "total": 3.99},  # subtotal doesn't match the items
        {"items": []},  # an order needs at least one item
        {
            "items": [
                {"menu_item_id": "item_001", "name": "Salmon Nigiri", "unit_price": 6.50, "quantity": 2, "line_total": 1.00}
            ]
        },  # line total doesn't match price * quantity
    ],
)
def test_create_rejects_inconsistent_totals_and_changes_nothing(order_file, bad_change):
    before = order_file.read_text(encoding="utf-8")
    with pytest.raises(InvalidOrderError):
        OrderRepository(order_file).create({**ORDER_INPUT, **bad_change})
    assert order_file.read_text(encoding="utf-8") == before


def test_create_rejects_missing_customer(order_file):
    data = {k: v for k, v in ORDER_INPUT.items() if k != "customer_id"}
    with pytest.raises(InvalidOrderError):
        OrderRepository(order_file).create(data)


# Reading


def test_get_by_customer_returns_only_their_orders_newest_first(order_file):
    repo = OrderRepository(order_file)
    first = repo.create(ORDER_INPUT)
    second = repo.create(ORDER_INPUT)
    orders = repo.get_by_customer("cust_001")
    assert [o["id"] for o in orders] == [second["id"], first["id"]]
    assert repo.get_by_customer("cust_404") == []


def test_get_by_id_returns_none_for_unknown_id(order_file):
    assert OrderRepository(order_file).get_by_id("ord_404") is None


def test_orders_cannot_be_updated():
    assert not hasattr(OrderRepository, "update")


# Invalid data files


def test_missing_file_raises(tmp_path):
    with pytest.raises(OrderDataError, match="not found"):
        OrderRepository(tmp_path / "nope.json").get_all()


def test_order_with_wrong_total_in_file_raises(tmp_path):
    path = tmp_path / "orders.json"
    path.write_text(json.dumps([{**EXISTING_ORDER, "total": 1.00}]), encoding="utf-8")
    with pytest.raises(OrderDataError, match="invalid"):
        OrderRepository(path).get_all()


def test_duplicate_order_ids_raise(tmp_path):
    path = tmp_path / "orders.json"
    path.write_text(json.dumps([EXISTING_ORDER, EXISTING_ORDER]), encoding="utf-8")
    with pytest.raises(OrderDataError, match="Duplicate order ID"):
        OrderRepository(path).get_all()


# Committed representative data (read-only check)


def test_committed_seed_orders_are_valid():
    assert OrderRepository("data/orders.json").get_all()