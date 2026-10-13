from app.repositories.menu_item_repository import MenuItemRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.menu import Menu
from app.schemas.menu_item import MenuItem
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

    def get_restaurant(self, restaurant_id: str) -> Restaurant:
        restaurant = self.restaurant_repository.get_by_id(restaurant_id)
        if restaurant is None:
            raise RestaurantNotFoundError(restaurant_id)
        return Restaurant(**restaurant)

    def get_menu(self, restaurant_id: str) -> Menu:
        self.get_restaurant(restaurant_id)
        items = self.menu_item_repository.get_by_restaurant(restaurant_id)
        return Menu(
            restaurant_id=restaurant_id,
            items=[MenuItem(**item) for item in items],
        )

    def get_menu_item(self, restaurant_id: str, item_id: str) -> MenuItem:
        self.get_restaurant(restaurant_id)
        item = self.menu_item_repository.get_by_id(item_id)
        if item is None or item["restaurant_id"] != restaurant_id:
            raise MenuItemNotFoundError(item_id)
        return MenuItem(**item)
