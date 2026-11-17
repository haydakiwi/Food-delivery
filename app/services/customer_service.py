"""Customer account business rules, independent of HTTP routing."""

from collections.abc import Callable

from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerCreate, CustomerPublic, CustomerUpdate
from app.services.auth_service import hash_password


class CustomerNotFoundError(LookupError):
    """Raised when the requested customer does not exist."""


class CustomerService:
    def __init__(
        self,
        customer_repository: CustomerRepository,
        password_hasher: Callable[[str], str] = hash_password,
    ) -> None:
        self.customer_repository = customer_repository
        self._password_hasher = password_hasher

    def register(self, data: CustomerCreate) -> CustomerPublic:
        """Hash the password before the persistence boundary is crossed."""
        record = data.model_dump(exclude={"password"})
        record["password_hash"] = self._password_hasher(data.password)
        created = self.customer_repository.create(record)
        return CustomerPublic(**created)

    def get_customer(self, customer_id: str) -> CustomerPublic:
        record = self.customer_repository.get_by_id(customer_id)
        if record is None:
            raise CustomerNotFoundError(customer_id)
        return CustomerPublic(**record)

    def update_customer(
        self, customer_id: str, data: CustomerUpdate
    ) -> CustomerPublic:
        changes = data.model_dump(exclude_unset=True)
        updated = self.customer_repository.update(customer_id, changes)
        if updated is None:
            raise CustomerNotFoundError(customer_id)
        return CustomerPublic(**updated)

    def deactivate_customer(self, customer_id: str) -> CustomerPublic:
        updated = self.customer_repository.deactivate(customer_id)
        if updated is None:
            raise CustomerNotFoundError(customer_id)
        return CustomerPublic(**updated)
