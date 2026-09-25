from app.schemas.restaurant import Restaurant
from app.services.restaurant_service import RestaurantService


class FakeRestaurantRepository:
    def get_all(self):
        return [
            {
                "id": "test_001",
                "name": "Test Sushi",
                "cuisine": "Japanese",
                "rating": 4.5,
                "delivery_time_minutes": 30,
                "delivery_fee": 2.99,
                "is_open": True,
                "address": "123 Test Street",
            }
        ]


def test_get_all_restaurants_returns_restaurant_models():
    repository = FakeRestaurantRepository()
    service = RestaurantService(repository)

    restaurants = service.get_all_restaurants()

    assert len(restaurants) == 1
    assert isinstance(restaurants[0], Restaurant)
    assert restaurants[0].id == "test_001"
    assert restaurants[0].name == "Test Sushi"