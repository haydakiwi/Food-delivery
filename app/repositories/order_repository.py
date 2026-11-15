from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from app.repositories.json_repository import JsonRepository, RepositoryDataError
from app.schemas.order import Order, OrderCreate


class OrderDataError(RepositoryDataError):
    """Raised when the order data file is missing or malformed."""


class InvalidOrderError(ValueError):
    """Raised when order data is incomplete or its totals don't add up."""


class OrderRepository(JsonRepository):
    """Single owner of orders.json (path from ORDERS_PATH).

    Orders are append-only in M2: there is no update or delete, so a saved
    order always shows exactly what the customer was charged.
    """

    entity_name = "order"
    id_prefix = "ord"
    error_class = OrderDataError
    required_fields = ("customer_id", "restaurant_id", "items", "total")

    def create(self, order_data: dict[str, Any] | OrderCreate) -> dict[str, Any]:
        """Validate and save a new order, returning it with its new ID.

        Raises InvalidOrderError (and writes nothing) if the totals are wrong
        or required data is missing.
        """
        try:
            order = (
                order_data
                if isinstance(order_data, OrderCreate)
                else OrderCreate(**order_data)
            )
        except ValidationError as exc:
            raise InvalidOrderError(str(exc)) from exc

        record = {
            **order.model_dump(mode="json"),
            "status": "placed",
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        return self._insert(record)

    def get_by_customer(self, customer_id: str) -> list[dict[str, Any]]:
        """Return a customer's orders, newest first."""
        orders = [o for o in self._load() if o["customer_id"] == customer_id]
        return sorted(orders, key=lambda o: (o["created_at"], o["id"]), reverse=True)

    def _load(self) -> list[dict[str, Any]]:
        orders = super()._load()
        for index, order in enumerate(orders):
            try:
                Order(**order)
            except ValidationError as exc:
                raise OrderDataError(
                    f"Order at position {index} is invalid: {exc.errors()[0]['msg']}"
                ) from exc
        return orders