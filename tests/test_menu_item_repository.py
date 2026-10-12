import json
import pytest
from app.repositories.menu_item_repository import MenuItemDataError, MenuItemRepository

SAMPLE_ITEMS = [
    {"id": "item_001", "restaurant_id": "rest_001", "name": "Salmon Nigiri", "price": 6.5, "category": "Sushi"},
    {"id": "item_002", "restaurant_id": "rest_001", "name": "Miso Soup", "price": 3.5, "category": "Sides"},
    {"id": "item_003", "restaurant_id": "rest_002", "name": "Fries", "price": 4.99, "category": "Sides"},
]

@pytest.fixture
def menu_file(tmp_path):
    """Create a temporary JSON file with sample menu item data."""
    path = tmp_path / "menu_items.json"
    path.write_text(json.dumps(SAMPLE_ITEMS), encoding="utf-8")
    return path

"""Reading data tests"""

def test_get_all_returns_every_item(menu_file):
    assert MenuItemRepository(menu_file).get_all() == SAMPLE_ITEMS

def test_get_by_id_returns_matching_item(menu_file):
    assert MenuItemRepository(menu_file).get_by_id("item_003")["name"] == "Fries"

def test_get_by_id_returns_none_for_unknown_id(menu_file):
    assert MenuItemRepository(menu_file).get_by_id("item_999") is None

def test_get_by_restaurant_returns_only_that_restaurants_items(menu_file):
    items = MenuItemRepository(menu_file).get_by_restaurant("rest_001")
    assert [item["id"] for item in items] == ["item_001", "item_002"]

def test_get_by_restaurant_returns_empty_list_when_no_items(menu_file):
    assert MenuItemRepository(menu_file).get_by_restaurant("rest_404") == []

"""Writing data tests"""

def test_create_assigns_next_id_and_restaurant(menu_file):
    new = MenuItemRepository(menu_file).create("rest_002", {"name": "Burger", "price": 12.99, "category": "Burgers"})
    assert new["id"] == "item_004"
    assert new["restaurant_id"] == "rest_002"

def test_create_ignores_id_and_restaurant_sent_in_data(menu_file):
    new = MenuItemRepository(menu_file).create(
        "rest_002", {"id": "item_001", "restaurant_id": "rest_001", "name": "Sneaky"}
    )
    assert new["id"] == "item_004"
    assert new["restaurant_id"] == "rest_002"

def test_created_item_survives_restart(menu_file):
    MenuItemRepository(menu_file).create("rest_002", {"name": "Burger"})
    restarted = MenuItemRepository(menu_file)
    assert restarted.get_by_id("item_004")["name"] == "Burger"
    assert len(restarted.get_by_restaurant("rest_002")) == 2

def test_update_changes_only_given_fields(menu_file):
    repo = MenuItemRepository(menu_file)
    updated = repo.update("item_003", {"price": 5.49})
    assert updated["price"] == 5.49
    assert updated["name"] == "Fries"
    assert MenuItemRepository(menu_file).get_by_id("item_003")["price"] == 5.49

def test_update_cannot_change_id_or_restaurant(menu_file):
    updated = MenuItemRepository(menu_file).update(
        "item_001", {"id": "item_999", "restaurant_id": "rest_002", "name": "Renamed"}
    )
    assert updated["id"] == "item_001"
    assert updated["restaurant_id"] == "rest_001"
    assert updated["name"] == "Renamed"

def test_update_unknown_id_returns_none_and_changes_nothing(menu_file):
    before = menu_file.read_text(encoding="utf-8")
    assert MenuItemRepository(menu_file).update("item_999", {"price": 1.0}) is None
    assert menu_file.read_text(encoding="utf-8") == before


# Failure cases

def test_missing_file_raises(tmp_path):
    with pytest.raises(MenuItemDataError, match="not found"):
        MenuItemRepository(tmp_path / "nope.json").get_all()

def test_invalid_json_raises(tmp_path):
    path = tmp_path / "menu_items.json"
    path.write_text("{ not json", encoding="utf-8")
    with pytest.raises(MenuItemDataError, match="Invalid JSON"):
        MenuItemRepository(path).get_all()

def test_duplicate_ids_raise(tmp_path):
    path = tmp_path / "menu_items.json"
    path.write_text(json.dumps([SAMPLE_ITEMS[0], SAMPLE_ITEMS[0]]), encoding="utf-8")
    with pytest.raises(MenuItemDataError, match="Duplicate menu item ID"):
        MenuItemRepository(path).get_all()

def test_item_without_restaurant_id_raises(tmp_path):
    path = tmp_path / "menu_items.json"
    path.write_text(json.dumps([{"id": "item_001", "name": "Orphan"}]), encoding="utf-8")
    with pytest.raises(MenuItemDataError, match="restaurant_id"):
        MenuItemRepository(path).get_all()