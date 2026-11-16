import json
from pathlib import Path

import pytest

from app.repositories.customer_repository import (
    CustomerRepository,
    DuplicateCustomerEmailError,
)
from app.schemas.customer import CustomerCreate, CustomerUpdate, DeliveryAddress
from app.services.customer_service import CustomerNotFoundError, CustomerService


@pytest.fixture
def service_and_path(tmp_path: Path):
    path = tmp_path / "customers.json"
    path.write_text("[]", encoding="utf-8")
    service = CustomerService(
        CustomerRepository(path), password_hasher=lambda password: f"hashed:{password}"
    )
    return service, path


def test_register_hashes_before_repository_and_returns_public_model(service_and_path):
    service, path = service_and_path
    customer = service.register(
        CustomerCreate(
            name="Shukan",
            email=" Shukan@Example.com ",
            password="Password123!",
        )
    )

    stored = json.loads(path.read_text(encoding="utf-8"))[0]
    assert stored["password_hash"] == "hashed:Password123!"
    assert "password" not in stored
    assert customer.email == "shukan@example.com"
    assert "password_hash" not in customer.model_dump()


def test_update_profile_and_addresses(service_and_path):
    service, _path = service_and_path
    customer = service.register(
        CustomerCreate(name="A", email="a@example.com", password="Password123!")
    )
    updated = service.update_customer(
        customer.id,
        CustomerUpdate(
            name="Alice",
            addresses=[
                DeliveryAddress(
                    label="Home",
                    street="1 Main St",
                    city="Kelowna",
                    province="BC",
                    postal_code="V1V 1V1",
                    is_default=True,
                )
            ],
        ),
    )

    assert updated.name == "Alice"
    assert updated.addresses[0].city == "Kelowna"


def test_duplicate_email_and_unknown_customer_errors(service_and_path):
    service, _path = service_and_path
    service.register(
        CustomerCreate(name="A", email="a@example.com", password="Password123!")
    )
    with pytest.raises(DuplicateCustomerEmailError):
        service.register(
            CustomerCreate(name="B", email="A@example.com", password="Password123!")
        )
    with pytest.raises(CustomerNotFoundError):
        service.update_customer("cust_999", CustomerUpdate(name="Nobody"))
