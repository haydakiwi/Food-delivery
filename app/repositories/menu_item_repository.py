from typing import Any

from app.repositories.json_repository import JsonRepository, RepositoryDataError


class MenuItemDataError(RepositoryDataError):
    """Raised when the menu item data file is missing or malformed."""


class MenuItemRepository(JsonRepository):
    """Single owner of menu_items.json — source of truth for prices and availability."""

    entity_name = "menu item"
    id_prefix = "item"
    error_class = MenuItemDataError
    required_fields = ("restaurant_id",)
    protected_fields = frozenset({"id", "restaurant_id"})

    def get_by_restaurant(self, restaurant_id: str) -> list[dict[str, Any]]:
        """Return every menu item belonging to one restaurant."""
        return [item for item in self._load() if item["restaurant_id"] == restaurant_id]

    def create(self, restaurant_id: str, item_data: dict[str, Any]) -> dict[str, Any]:
        """Create a menu item for a restaurant; caller-sent IDs are ignored."""
        return self._insert({**item_data, "restaurant_id": restaurant_id})

    def update(self, item_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        """Update a menu item; id and restaurant_id can never change."""
        return self._update_record(item_id, changes)