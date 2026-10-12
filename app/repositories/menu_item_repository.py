import json
import os
from pathlib import Path
from typing import Any

class MenuItemDataError(Exception):
    """Raised when the menu item data file is missing or malformed."""

class MenuItemRepository:
    def __init__(self, data_path: Path | str) -> None:
        self.data_path = Path(data_path)

    def get_all(self) -> list[dict[str, Any]]:
        """Return all menu items."""
        return self._load()

    def get_by_id(self, item_id: str) -> dict[str, Any] | None:
        """Return a menu item by its ID, or None if not found."""
        items = self._load()
        for item in items:
            if item.get("id") == item_id:
                return item
        return None

    def get_by_restaurant(self, restaurant_id: str) -> list[dict[str, Any]]:

        return [item for item in self._load() if item["restaurant_id"] == restaurant_id]

    def create(self, restaurant_id: str, item_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new menu item for a restaurant."""
        items = self._load()
        new_item = {**item_data, "id": self._next_id(items), "restaurant_id": restaurant_id}
        items.append(new_item)
        self._save(items)
        return new_item

    def update(self, item_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        """Update an existing menu item"""
        items = self._load()
        for item in items:
            if item["id"] == item_id:
                changes = {key: value for key, value in changes.items()
                           if key not in ("id", "restaurant_id")}
                item.update(changes)
                self._save(items)
                return item
        return None

    def _next_id(self, items: list[dict[str, Any]]) -> str:

        numbers = []
        for item in items:
            prefix, _, number = item["id"].partition("_")
            if prefix == "item" and number.isdigit():
                numbers.append(int(number))
        return f"item_{max(numbers, default=0) + 1:03d}"

    def _save(self, items: list[dict[str, Any]]) -> None:

        temp_path = self.data_path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(items, f, indent=4)
        os.replace(temp_path, self.data_path)

    def _load(self) -> list[dict[str, Any]]:
        if not self.data_path.exists():
            raise MenuItemDataError(f"Data file not found: {self.data_path}")
        try:
            with self.data_path.open(encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            raise MenuItemDataError(f"Invalid JSON in {self.data_path}: {exc.msg}") from exc
        if not isinstance(data, list):
            raise MenuItemDataError("Menu item data must be a JSON list")

        seen_ids: set[str] = set()
        for index, item in enumerate(data):
            if not isinstance(item, dict) or "id" not in item or "restaurant_id" not in item:
                raise MenuItemDataError(
                    f"Menu item at position {index} is missing an 'id' or 'restaurant_id'"
                )
            if item["id"] in seen_ids:
                raise MenuItemDataError(f"Duplicate menu item ID found: '{item['id']}' at position {index}")
            seen_ids.add(item["id"])
        return data