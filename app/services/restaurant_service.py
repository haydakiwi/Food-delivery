from app.repositories.menu_item_repository import MenuItemRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.restaurant import Restaurant


class RestaurantNotFoundError(LookupError):
    """Raised when a requested restaurant does not exist."""


class MenuItemNotFoundError(LookupError):
    """Raised when a requested menu item does not exist for a restaurant."""


class RestaurantService:
    def __init__(
        self,
        restaurant_repository: RestaurantRepository,
        menu_item_repository: MenuItemRepository,
    ) -> None:
        self.restaurant_repository = restaurant_repository
        self.menu_item_repository = menu_item_repository

    def get_all_restaurants(
        self,
        search: str | None = None,
        cuisine: str | None = None,
        is_open: bool | None = None,
    ) -> list[Restaurant]:
        restaurants = self.restaurant_repository.get_all()

        if search:
            normalized_search = search.casefold()
            restaurants = [
                restaurant
                for restaurant in restaurants
                if normalized_search in restaurant["name"].casefold()
            ]

        if cuisine:
            normalized_cuisine = cuisine.casefold()
            restaurants = [
                restaurant
                for restaurant in restaurants
                if restaurant["cuisine"].casefold() == normalized_cuisine
            ]

        if is_open is not None:
            restaurants = [
                restaurant
                for restaurant in restaurants
                if restaurant["is_open"] is is_open
            ]

        return [Restaurant(**restaurant) for restaurant in restaurants]