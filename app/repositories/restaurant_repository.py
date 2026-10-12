import json 
import os
from pathlib import Path
from typing import Any

class RestaurantDataError(Exception):
    """Raised when the restaurant data file is missing or malformed."""

class RestaurantRepository:
    def __init__(self, data_path: Path | str) -> None:
        self.data_path = Path(data_path)

    def get_all(self) -> list[dict[str, Any]]:
        """Return every restaurant in the data file."""
        return self._load()

    def get_by_id(self, restaurant_id: str) -> dict[str, Any] | None:
        """Return a restaurant by its ID."""
        for restaurant in self._load():
            if restaurant["id"] == restaurant_id:
                return restaurant
        return None    

    def create(self, restaurant_data: dict[str, Any]) -> dict[str, Any]:
        """Create a new restaurant and return it."""
        restaurants = self._load()
        new_restaurant = {**restaurant_data, "id": self._next_id(restaurants)}
        restaurants.append(new_restaurant)
        self._save(restaurants)
        return new_restaurant

    def update(self, restaurant_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        """Update an existing restaurant and return it."""
        restaurants = self._load()
        for restaurant in restaurants:
            if restaurant["id"] == restaurant_id:
                changes = {key: value for key, value in changes.items() if key != "id"}
                restaurant.update(changes)
                self._save(restaurants)
                return restaurant
        return None

    def _next_id(self, restaurants: list[dict[str, Any]]) -> str:

        numbers = []
        for restaurant in restaurants:
            prefix, _, number = restaurant["id"].partition("_")
            if prefix == "rest" and number.isdigit():
                numbers.append(int(number))
        next_number = max(numbers, default=0) + 1
        return f"rest_{next_number:03d}"

    def _save(self, restaurants: list[dict[str, Any]]) -> None:
        temp_path = self.data_path.with_suffix(".tmp")
        with temp_path.open("w", encoding="utf-8") as f:
            json.dump(restaurants, f, indent=4)
        os.replace(temp_path, self.data_path)

    def _load(self) -> list[dict[str, Any]]:
        if not self.data_path.exists():
            raise RestaurantDataError(f"Data file not found: {self.data_path}")

        try: 
            with self.data_path.open(encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as exc:
            raise RestaurantDataError(
                f"Invalid JSON in {self.data_path}: {exc.msg}"
            ) from exc
        if not isinstance(data, list):
            raise RestaurantDataError("Restaurant data must be a JSON list")

        seen_ids: set[str] = set()
        for index, item in enumerate(data):
            if not isinstance(item, dict) or "id" not in item:
                raise RestaurantDataError(
                    f"Restaurant at position {index} is missing an 'id'"
                )
            if item["id"] in seen_ids:
                raise RestaurantDataError(
                    f"Duplicate restaurant ID '{item['id']}' found at position {index}"
                )
            seen_ids.add(item["id"])
        return data
    """The tests are checking if the file exists,
    if it does, it checks if the file is a valid JSON,
    if it is a valid JSON, it checks if the data is a list,
    if it is a list, it checks if every restaurant has a unique ID"""