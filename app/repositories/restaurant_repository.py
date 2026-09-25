import json
from pathlib import Path
from typing import Any

class RestaruantDataError(Exception):
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

    def _load(self) -> list[dict[str, Any]]:
        if not self.data_path.exists():
            raise RestaurantDataError(f"Data file not found: {self.data_path}")

        try: 
            with self.data_path.open(encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
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