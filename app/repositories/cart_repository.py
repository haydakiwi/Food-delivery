from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from app.repositories.json_repository import JsonRepository, RepositoryDataError
from app.schemas.cart import Cart


class CartDataError(RepositoryDataError):
    """Raised when the cart data file is missing or malformed."""


class ActiveCartExistsError(ValueError):
    """Raised when a customer already has an active cart."""


class CartNotActiveError(ValueError):
    """Raised when changing a cart that is checked out or abandoned."""


class InvalidCartError(ValueError):
    """Raised when a change would leave the cart invalid (e.g. quantity 0)."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class CartRepository(JsonRepository):
    """Single owner of carts.json (path from CARTS_PATH).

    Business rules that need other data (item availability, one restaurant
    per cart, customer is active) belong in the cart service. This repository
    only guarantees what it can check from cart data alone: one active cart
    per customer, valid quantities, and no edits to closed carts.
    """

    entity_name = "cart"
    id_prefix = "cart"
    error_class = CartDataError
    required_fields = ("customer_id", "status", "items")
    # status only changes through close(); owner and creation time never change.
    protected_fields = frozenset({"id", "customer_id", "created_at", "status"})

    def get_by_customer(self, customer_id: str) -> list[dict[str, Any]]:
        """Return every cart (any status) belonging to a customer."""
        return [cart for cart in self._load() if cart["customer_id"] == customer_id]

    def get_active_by_customer(self, customer_id: str) -> dict[str, Any] | None:
        """Return the customer's active cart, or None if they don't have one."""
        for cart in self._load():
            if cart["customer_id"] == customer_id and cart["status"] == "active":
                return cart
        return None

    def create(self, customer_id: str) -> dict[str, Any]:
        """Create an empty active cart. A customer may have only one."""
        if self.get_active_by_customer(customer_id) is not None:
            raise ActiveCartExistsError(customer_id)
        timestamp = _now()
        return self._insert(
            {
                "customer_id": customer_id,
                "restaurant_id": None,
                "items": [],
                "status": "active",
                "created_at": timestamp,
                "updated_at": timestamp,
            }
        )

    def update(self, cart_id: str, changes: dict[str, Any]) -> dict[str, Any] | None:
        """Change items and/or restaurant_id of an active cart.

        The result is validated before saving, so a rejected change leaves
        the file untouched. Returns None if the cart does not exist.
        """
        existing = self.get_by_id(cart_id)
        if existing is None:
            return None
        if existing["status"] != "active":
            raise CartNotActiveError(cart_id)

        allowed = {k: v for k, v in changes.items() if k not in self.protected_fields}
        allowed["updated_at"] = _now()
        try:
            Cart(**{**existing, **allowed})
        except ValidationError as exc:
            raise InvalidCartError(str(exc)) from exc
        return self._update_record(cart_id, allowed)

    def clear(self, cart_id: str) -> dict[str, Any] | None:
        """Remove every item, so the cart can be used for any restaurant."""
        return self.update(cart_id, {"items": [], "restaurant_id": None})

    def close(self, cart_id: str, status: str = "checked_out") -> dict[str, Any] | None:
        """Close an active cart after checkout (or mark it abandoned).

        Checkout must call this only AFTER the order has been saved.
        """
        if status not in ("checked_out", "abandoned"):
            raise ValueError(f"Cannot close a cart with status '{status}'")
        existing = self.get_by_id(cart_id)
        if existing is None:
            return None
        if existing["status"] != "active":
            raise CartNotActiveError(cart_id)

        records = self._load()
        for record in records:
            if record["id"] == cart_id:
                record["status"] = status
                record["updated_at"] = _now()
                self._save(records)
                return record
        return None

    def _load(self) -> list[dict[str, Any]]:
        carts = super()._load()
        active_owners: set[str] = set()
        for index, cart in enumerate(carts):
            try:
                Cart(**cart)
            except ValidationError as exc:
                raise CartDataError(
                    f"Cart at position {index} is invalid: {exc.errors()[0]['msg']}"
                ) from exc
            if cart["status"] == "active":
                if cart["customer_id"] in active_owners:
                    raise CartDataError(
                        f"Customer '{cart['customer_id']}' has more than one active cart"
                    )
                active_owners.add(cart["customer_id"])
        return carts