import json

import pytest

from app.repositories.cart_repository import (
    ActiveCartExistsError,
    CartDataError,
    CartNotActiveError,
    CartRepository,
    InvalidCartError,
)

SAMPLE_CARTS = [
    {
        "id": "cart_001",
        "customer_id": "cust_001",
        "restaurant_id": "rest_001",
        "items": [{"menu_item_id": "item_001", "quantity": 2}],
        "status": "active",
        "created_at": "2026-11-10T00:00:00+00:00",
        "updated_at": "2026-11-10T00:00:00+00:00",
    },
    {
        "id": "cart_002",
        "customer_id": "cust_002",
        "restaurant_id": "rest_002",
        "items": [{"menu_item_id": "item_003", "quantity": 1}],
        "status": "checked_out",
        "created_at": "2026-11-09T00:00:00+00:00",
        "updated_at": "2026-11-09T00:00:00+00:00",
    },
]


@pytest.fixture
def cart_file(tmp_path):
    """Temporary carts.json so committed data is never touched."""
    path = tmp_path / "carts.json"
    path.write_text(json.dumps(SAMPLE_CARTS), encoding="utf-8")
    return path


# Reading


def test_get_by_id_returns_matching_cart(cart_file):
    assert CartRepository(cart_file).get_by_id("cart_002")["customer_id"] == "cust_002"


def test_get_active_by_customer_returns_active_cart(cart_file):
    assert CartRepository(cart_file).get_active_by_customer("cust_001")["id"] == "cart_001"


def test_get_active_by_customer_ignores_checked_out_carts(cart_file):
    assert CartRepository(cart_file).get_active_by_customer("cust_002") is None


def test_get_by_customer_returns_all_statuses(cart_file):
    assert [c["id"] for c in CartRepository(cart_file).get_by_customer("cust_002")] == [
        "cart_002"
    ]


# Creating


def test_create_makes_empty_active_cart(cart_file):
    cart = CartRepository(cart_file).create("cust_002")
    assert cart["id"] == "cart_003"
    assert cart["status"] == "active"
    assert cart["items"] == []
    assert cart["restaurant_id"] is None


def test_create_rejects_second_active_cart_and_changes_nothing(cart_file):
    before = cart_file.read_text(encoding="utf-8")
    with pytest.raises(ActiveCartExistsError):
        CartRepository(cart_file).create("cust_001")
    assert cart_file.read_text(encoding="utf-8") == before


def test_created_cart_survives_restart(cart_file):
    CartRepository(cart_file).create("cust_003")
    restarted = CartRepository(cart_file)
    assert restarted.get_active_by_customer("cust_003")["id"] == "cart_003"


# Updating


def test_update_replaces_items(cart_file):
    repo = CartRepository(cart_file)
    items = [
        {"menu_item_id": "item_001", "quantity": 3},
        {"menu_item_id": "item_002", "quantity": 1},
    ]
    updated = repo.update("cart_001", {"items": items})
    assert updated["items"] == items
    assert CartRepository(cart_file).get_by_id("cart_001")["items"] == items


def test_update_sets_restaurant_on_empty_cart(cart_file):
    repo = CartRepository(cart_file)
    cart = repo.create("cust_002")
    updated = repo.update(
        cart["id"],
        {"restaurant_id": "rest_003", "items": [{"menu_item_id": "item_005", "quantity": 1}]},
    )
    assert updated["restaurant_id"] == "rest_003"


@pytest.mark.parametrize("quantity", [0, -1, 51])
def test_update_rejects_invalid_quantity_and_changes_nothing(cart_file, quantity):
    before = cart_file.read_text(encoding="utf-8")
    with pytest.raises(InvalidCartError):
        CartRepository(cart_file).update(
            "cart_001", {"items": [{"menu_item_id": "item_001", "quantity": quantity}]}
        )
    assert cart_file.read_text(encoding="utf-8") == before


def test_update_rejects_same_item_twice(cart_file):
    with pytest.raises(InvalidCartError):
        CartRepository(cart_file).update(
            "cart_001",
            {
                "items": [
                    {"menu_item_id": "item_001", "quantity": 1},
                    {"menu_item_id": "item_001", "quantity": 2},
                ]
            },
        )


def test_update_rejects_items_without_restaurant(cart_file):
    with pytest.raises(InvalidCartError):
        CartRepository(cart_file).update("cart_001", {"restaurant_id": None})


def test_update_cannot_change_owner_or_status(cart_file):
    updated = CartRepository(cart_file).update(
        "cart_001", {"customer_id": "cust_999", "status": "checked_out", "id": "cart_999"}
    )
    assert updated["customer_id"] == "cust_001"
    assert updated["status"] == "active"
    assert updated["id"] == "cart_001"


def test_update_checked_out_cart_is_rejected(cart_file):
    with pytest.raises(CartNotActiveError):
        CartRepository(cart_file).update("cart_002", {"items": []})


def test_update_unknown_cart_returns_none_and_changes_nothing(cart_file):
    before = cart_file.read_text(encoding="utf-8")
    assert CartRepository(cart_file).update("cart_404", {"items": []}) is None
    assert cart_file.read_text(encoding="utf-8") == before


# Clearing and closing


def test_clear_empties_items_and_restaurant(cart_file):
    cleared = CartRepository(cart_file).clear("cart_001")
    assert cleared["items"] == []
    assert cleared["restaurant_id"] is None
    assert cleared["status"] == "active"


def test_close_marks_cart_checked_out_and_allows_new_cart(cart_file):
    repo = CartRepository(cart_file)
    closed = repo.close("cart_001")
    assert closed["status"] == "checked_out"
    assert closed["items"], "closed cart keeps its items as a record"
    assert repo.get_active_by_customer("cust_001") is None
    assert repo.create("cust_001")["id"] == "cart_003"


def test_close_already_closed_cart_is_rejected(cart_file):
    with pytest.raises(CartNotActiveError):
        CartRepository(cart_file).close("cart_002")


def test_close_rejects_unknown_status(cart_file):
    with pytest.raises(ValueError):
        CartRepository(cart_file).close("cart_001", status="active")


# Invalid data files


def test_missing_file_raises(tmp_path):
    with pytest.raises(CartDataError, match="not found"):
        CartRepository(tmp_path / "nope.json").get_all()


def test_two_active_carts_for_one_customer_in_file_raise(tmp_path):
    path = tmp_path / "carts.json"
    second = {**SAMPLE_CARTS[0], "id": "cart_009"}
    path.write_text(json.dumps([SAMPLE_CARTS[0], second]), encoding="utf-8")
    with pytest.raises(CartDataError, match="more than one active cart"):
        CartRepository(path).get_all()


def test_invalid_quantity_in_file_raises(tmp_path):
    path = tmp_path / "carts.json"
    bad = {**SAMPLE_CARTS[0], "items": [{"menu_item_id": "item_001", "quantity": 0}]}
    path.write_text(json.dumps([bad]), encoding="utf-8")
    with pytest.raises(CartDataError, match="invalid"):
        CartRepository(path).get_all()


def test_cart_without_customer_raises(tmp_path):
    path = tmp_path / "carts.json"
    bad = {k: v for k, v in SAMPLE_CARTS[0].items() if k != "customer_id"}
    path.write_text(json.dumps([bad]), encoding="utf-8")
    with pytest.raises(CartDataError, match="customer_id"):
        CartRepository(path).get_all()


# Committed representative data (read-only check)


def test_committed_seed_carts_are_valid():
    carts = CartRepository("data/carts.json").get_all()
    assert any(c["status"] == "active" for c in carts)