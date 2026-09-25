from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.restaurant import Restaurant


class RestaurantService:
    def __init__(self, repository: RestaurantRepository) -> None:
        self.repository = repository

    def get_all_restaurants(self) -> list[Restaurant]:
        restaurants = self.repository.get_all()
        return [Restaurant(**restaurant) for restaurant in restaurants]