import json 
import pytest

from app.repositories.restaurant_repository import (
RestaurantRepository, RestaurantDataError
)

SAMPLE_RESTAURANTS = [
    {"id": "test_001", "name": "Test Sushi", "cuisine": "Japanese", "rating": "4.5"},
    {"id": "test_002", "name": "Test Burger", "cuisine": "American", "rating": "4.0"}
]
WRITABLE_RESTAURANTS = [
    {"id": "rest_001", "name": "Test Sushi", "cuisine": "Japanese"},
    {"id": "rest_002", "name": "Test Burger", "cuisine": "American"},
]

@pytest.fixture
def data_file(tmp_path):
    """Create a temporary JSON file with sample restaurant data."""
    path = tmp_path / "restaurants.json"
    path.write_text(json.dumps(SAMPLE_RESTAURANTS), encoding="utf-8")
    return path

def test_get_all_returns_all_restaurants(data_file):
    repo = RestaurantRepository(data_file)
    restaurants = repo.get_all()
    assert restaurants == SAMPLE_RESTAURANTS

def test_get_by_id_returns_none_for_unknown_id(data_file):
    repo = RestaurantRepository(data_file)
    assert repo.get_by_id("test_002")["name"] == "Test Burger"

def test_get_by_id_returns_restaurant_for_unknown_id(data_file):
    repo = RestaurantRepository(data_file)
    assert repo.get_by_id("does_not_exist") is None
    """Assert means that the condition must be true, or else the test fails"""

"""Failure cases"""
def test_missing_file_raises(tmp_path):
    repo = RestaurantRepository(tmp_path / "nope.json")
    with pytest.raises(RestaurantDataError, match="not found"):
        repo.get_all()

def test_invalid_json_raises(tmp_path):
    path = tmp_path / "restaurants.json"
    path.write_text("{ this is not json", encoding ="utf-8")
    with pytest.raises(RestaurantDataError, match="Invalid JSON"):
        RestaurantRepository(path).get_all()
        
def test_duplicate_ids_raises(tmp_path):
    path = tmp_path / "restaurants.json"
    path.write_text(
        json.dumps([{"id": "dup", "name": "A"}, {"id": "dup", "name": "B"}]),
        encoding="utf-8"
    )
    with pytest.raises(RestaurantDataError, match="Duplicate restaurant ID"):
        RestaurantRepository(path).get_all()

def test_non_list_json_raises(tmp_path):
    path = tmp_path / "restaurants.json"
    path.write_text(json.dumps({"id": "x"}), encoding="utf-8")
    with pytest.raises(RestaurantDataError, match="must be a JSON list"):
        RestaurantRepository(path).get_all()

def test_restaurant_without_id_raises(tmp_path):
    path = tmp_path / "restaurants.json"
    path.write_text(json.dumps([{"name": "No ID"}]), encoding="utf-8")
    with pytest.raises(RestaurantDataError, match="missing an 'id'"):
        RestaurantRepository(path).get_all()

@pytest.fixture
def writable_file(tmp_path):

    path = tmp_path / "restaurants.json"
    path.write_text(json.dumps(WRITABLE_RESTAURANTS), encoding="utf-8")
    return path

def test_create_assigns_next_id(writable_file):
    repo = RestaurantRepository(writable_file)
    new = repo.create({"name": "Pho Place", "cuisine": "Vietnamese"})
    assert new["id"] == "rest_003"
    assert new["name"] == "Pho Place"

def test_create_ignores_id_sent_by_caller(writable_file):
    repo = RestaurantRepository(writable_file)
    new = repo.create({"id": "rest_001", "name": "Sneaky",})
    assert new["id"] == "rest_003"
    assert repo.get_by_id("rest_001")["name"] == "Test Sushi"

def test_create_never_reuses_an_id(tmp_path):
    path = tmp_path / "restaurants.json"
    path.write_text(json.dumps([{"id": "rest_001"}, {"id": "rest_005"}]), encoding="utf-8")
    new = RestaurantRepository(path).create({"name": "New"})
    assert new["id"] == "rest_006"

def test_first_restaurant_in_empty_file_gets_rest_001(tmp_path):
    path = tmp_path / "restaurants.json"
    path.write_text("[]", encoding="utf-8")
    assert RestaurantRepository(path).create({"name": "First"})["id"] == "rest_001"

def test_update_changes_only_given_fields(writable_file):
    RestaurantRepository(writable_file).create({"name": "Pho Place"})
    restarted = RestaurantRepository(writable_file)
    assert restarted.get_by_id("rest_003")["name"] == "Pho Place"
    assert len(restarted.get_all()) == 3

def test_created_restaurant_survives_restart(writable_file):
    repo = RestaurantRepository(writable_file)
    updated = repo.update("rest_002", {"name": "Better Burger"})
    assert updated["name"] == "Better Burger"
    assert updated["cuisine"] == "American"
    assert RestaurantRepository(writable_file).get_by_id("rest_002")["name"] == "Better Burger"


def test_update_cannot_change_id(writable_file):
    repo = RestaurantRepository(writable_file)
    updated = repo.update("rest_001", {"id": "rest_999", "name": "Renamed"})
    assert updated["id"] == "rest_001"
    assert repo.get_by_id("rest_999") is None

def test_update_unknown_id_returns_none_and_changes_nothing(writable_file):
    before = writable_file.read_text(encoding="utf-8")
    assert RestaurantRepository(writable_file).update("rest_404", {"name": "Ghost"}) is None
    assert writable_file.read_text(encoding="utf-8") == before

def test_save_leaves_no_temp_file(writable_file):
    RestaurantRepository(writable_file).create({"name": "Pho Place"})
    assert not writable_file.with_suffix(".tmp").exists()
