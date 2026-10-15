from app.repositories.menu_item_repository import MenuItemRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.menu import Menu
from app.schemas.menu_item import MenuItem, MenuItemCreate, MenuItemUpdate
from app.schemas.restaurant import Restaurant, RestaurantCreate, RestaurantUpdate


class RestaurantNotFoundError(LookupError):
    """Raised when a requested restaurant does not exist."""


class MenuItemNotFoundError(LookupError):
    """Raised when a requested menu item does not exist for a restaurant."""


class DuplicateRestaurantNameError(ValueError):
    """Raised when a restaurant with the same name already exists."""


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

    def create_restaurant(self, data: RestaurantCreate) -> Restaurant:
        """Create a restaurant after enforcing management business rules."""
        normalized_name = data.name.strip().casefold()

        for restaurant in self.restaurant_repository.get_all():
            if restaurant["name"].strip().casefold() == normalized_name:
                raise DuplicateRestaurantNameError(data.name)

        created = self.restaurant_repository.create(data.model_dump())
        return Restaurant(**created)

    def update_restaurant(
        self,
        restaurant_id: str,
        data: RestaurantUpdate,
    ) -> Restaurant:
        """Update an existing restaurant."""
        existing = self.restaurant_repository.get_by_id(restaurant_id)
        if existing is None:
            raise RestaurantNotFoundError(restaurant_id)

        changes = data.model_dump(exclude_unset=True)

        if "name" in changes:
            normalized_name = changes["name"].strip().casefold()

            for restaurant in self.restaurant_repository.get_all():
                if (
                    restaurant["id"] != restaurant_id
                    and restaurant["name"].strip().casefold() == normalized_name
                ):
                    raise DuplicateRestaurantNameError(changes["name"])

        updated = self.restaurant_repository.update(restaurant_id, changes)
        return Restaurant(**updated)

    def create_menu_item(
        self,
        restaurant_id: str,
        data: MenuItemCreate,
    ) -> MenuItem:
        """Add a menu item to an existing restaurant."""
        self.get_restaurant(restaurant_id)

        created = self.menu_item_repository.create(
            restaurant_id,
            data.model_dump(),
        )
        return MenuItem(**created)

    def update_menu_item(
        self,
        restaurant_id: str,
        item_id: str,
        data: MenuItemUpdate,
    ) -> MenuItem:
        """Update a menu item belonging to an existing restaurant."""
        self.get_restaurant(restaurant_id)

        existing = self.menu_item_repository.get_by_id(item_id)

        if existing is None or existing["restaurant_id"] != restaurant_id:
            raise MenuItemNotFoundError(item_id)

        changes = data.model_dump(exclude_unset=True)
        updated = self.menu_item_repository.update(item_id, changes)

        return MenuItem(**updated)