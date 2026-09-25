import json 
import pytest

from app.repositories.restaurant_repository import (
RestaurantRepository, RestaurantDataError
)

SAMPLE_RESTAURANTS = [
    {"id": "test_001", "name": "Test Sushi", "cuisine": "Japanese", "rating": "4.5"},
    {"id": "test_002", "name": "Test Burger", "cuisine": "American", "rating": "4.0"}
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