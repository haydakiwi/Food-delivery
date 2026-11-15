from typing import Any
from app.repositories.json_repository import JsonRepository, RepositoryDataError

class RestaurantDataError(RepositoryDataError):
    """Raised when the restaurant data file is missing or malformed."""

class RestaurantRepository(JsonRepository):
    entity_name = "restaurant"
    id_prefix = "rest"
    error_class = RestaurantDataError

    def create(self, restaurant_data: dict[str, Any]) -> dict[str, Any]:
        return self._insert(restaurant_data)
    
    def update(self, restaurant_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        return self._update_record(restaurant_id, changes)