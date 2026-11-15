from datetime import datetime, timezone
from typing import Any

from app.repositories.json_repository import JsonRepository, RepositoryDataError
from app.schemas.customer import normalize_email


class CustomerDataError(RepositoryDataError):
    """Raised when the customer data file is missing or malformed."""


class DuplicateCustomerEmailError(ValueError):
    """Raised when another customer already uses this email."""


class CustomerRepository(JsonRepository):
    """Single owner of customers.json (path from CUSTOMERS_PATH)."""

    entity_name = "customer"
    id_prefix = "cust"
    error_class = CustomerDataError
    required_fields = ("email",)
    protected_fields = frozenset({"id", "created_at"})

    def get_by_email(self, email: str) -> dict[str, Any] | None:
        """Find a customer by email, ignoring case and surrounding spaces."""
        wanted = normalize_email(email)
        for customer in self._load():
            if customer["email"] == wanted:
                return customer
        return None

    def create(self, customer_data: dict[str, Any]) -> dict[str, Any]:
        """Save a new customer. customer_data must already contain password_hash."""
        email = normalize_email(customer_data["email"])
        if self.get_by_email(email) is not None:
            raise DuplicateCustomerEmailError(email)

        record = {
            "role": "customer",
            "is_active": True,
            "addresses": [],
            **customer_data,
            "email": email,
            "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        return self._insert(record)

    def update(
        self, customer_id: str, changes: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Update a customer; id and created_at can never change."""
        changes = dict(changes)
        if "email" in changes:
            changes["email"] = normalize_email(changes["email"])
            existing = self.get_by_email(changes["email"])
            if existing is not None and existing["id"] != customer_id:
                raise DuplicateCustomerEmailError(changes["email"])
        return self._update_record(customer_id, changes)

    def deactivate(self, customer_id: str) -> dict[str, Any] | None:
        """Mark a customer inactive. The record is kept so old orders stay linked."""
        return self._update_record(customer_id, {"is_active": False})

    def _load(self) -> list[dict[str, Any]]:
        customers = super()._load()
        seen_emails: set[str] = set()
        for index, customer in enumerate(customers):
            email = normalize_email(str(customer["email"]))
            if email in seen_emails:
                raise CustomerDataError(
                    f"Duplicate customer email '{email}' found at position {index}"
                )
            seen_emails.add(email)
        return customers