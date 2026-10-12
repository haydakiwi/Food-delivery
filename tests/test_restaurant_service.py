import pytest

from app.schemas.menu import Menu
from app.schemas.menu_item import MenuItem
from app.schemas.restaurant import Restaurant
from app.services.restaurant_service import (
    MenuItemNotFoundError,
    RestaurantNotFoundError,
    RestaurantService,
)


class FakeRestaurantRepository:
    def __init__(self) -> None:
        self.restaurants = [
            {
                "id": "rest_001",
                "name": "Test Sushi",
                "cuisine": "Japanese",
                "rating": 4.5,
                "delivery_time_minutes": 30,
                "delivery_fee": 2.99,
                "is_open": True,
                "address": "123 Test Street",
            },
            {
                "id": "rest_002",
                "name": "Curry House",
                "cuisine": "Indian",
                "rating": 4.7,
                "delivery_time_minutes": 25,
                "delivery_fee": 3.99,
                "is_open": False,
                "address": "456 Test Avenue",
            },
        ]

    def get_all(self):
        return self.restaurants

    def get_by_id(self, restaurant_id: str):
        return next(
            (
                restaurant
                for restaurant in self.restaurants
                if restaurant["id"] == restaurant_id
            ),
            None,
        )


class FakeMenuItemRepository:
    def __init__(self) -> None:
        self.items = [
            {
                "id": "item_001",
                "restaurant_id": "rest_001",
                "name": "Salmon Roll",
                "description": "Salmon and avocado",
                "price": 10.99,
                "category": "Sushi",
                "is_available": True,
            },
            {
                "id": "item_002",
                "restaurant_id": "rest_002",
                "name": "Butter Chicken",
                "description": "Creamy tomato curry",
                "price": 16.99,
                "category": "Mains",
                "is_available": True,
            },
        ]

    def get_by_restaurant(self, restaurant_id: str):
        return [
            item for item in self.items if item["restaurant_id"] == restaurant_id
        ]

    def get_by_id(self, item_id: str):
        return next((item for item in self.items if item["id"] == item_id), None)


@pytest.fixture
def service() -> RestaurantService:
    return RestaurantService(FakeRestaurantRepository(), FakeMenuItemRepository())


def test_get_all_restaurants_returns_restaurant_models(
    service: RestaurantService,
) -> None:
    restaurants = service.get_all_restaurants()

    assert len(restaurants) == 2
    assert isinstance(restaurants[0], Restaurant)
    assert restaurants[0].id == "rest_001"


def test_search_is_case_insensitive(service: RestaurantService) -> None:
    restaurants = service.get_all_restaurants(search="SUSHI")

    assert [restaurant.id for restaurant in restaurants] == ["rest_001"]


def test_filters_can_be_combined(service: RestaurantService) -> None:
    restaurants = service.get_all_restaurants(cuisine="indian", is_open=False)

    assert [restaurant.id for restaurant in restaurants] == ["rest_002"]


def test_get_restaurant_returns_details(service: RestaurantService) -> None:
    restaurant = service.get_restaurant("rest_002")

    assert restaurant.name == "Curry House"


def test_get_restaurant_raises_for_unknown_id(service: RestaurantService) -> None:
    with pytest.raises(RestaurantNotFoundError):
        service.get_restaurant("rest_404")


def test_get_menu_returns_only_the_restaurants_items(
    service: RestaurantService,
) -> None:
    menu = service.get_menu("rest_001")

    assert isinstance(menu, Menu)
    assert menu.restaurant_id == "rest_001"
    assert [item.id for item in menu.items] == ["item_001"]


def test_get_menu_item_returns_a_model(service: RestaurantService) -> None:
    item = service.get_menu_item("rest_001", "item_001")

    assert isinstance(item, MenuItem)
    assert item.name == "Salmon Roll"


def test_get_menu_item_rejects_an_item_from_another_restaurant(
    service: RestaurantService,
) -> None:
    with pytest.raises(MenuItemNotFoundError):
        service.get_menu_item("rest_001", "item_002")
