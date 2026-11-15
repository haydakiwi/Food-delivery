import json

import pytest

from app.repositories.customer_repository import (
    CustomerDataError,
    CustomerRepository,
    DuplicateCustomerEmailError,
)
from app.schemas.customer import Customer, CustomerPublic

SAMPLE_CUSTOMERS = [
    {
        "id": "cust_001",
        "name": "Alice",
        "email": "alice@example.com",
        "password_hash": "hash-a",
        "role": "customer",
        "is_active": True,
        "addresses": [],
        "created_at": "2026-11-01T00:00:00+00:00",
    },
    {
        "id": "cust_002",
        "name": "Ben",
        "email": "ben@example.com",
        "password_hash": "hash-b",
        "role": "customer",
        "is_active": True,
        "addresses": [],
        "created_at": "2026-11-02T00:00:00+00:00",
    },
]

NEW_CUSTOMER = {"name": "Dana", "email": "dana@example.com", "password_hash": "hash-d"}


@pytest.fixture
def customer_file(tmp_path):
    """Temporary customers.json so committed data is never touched."""
    path = tmp_path / "customers.json"
    path.write_text(json.dumps(SAMPLE_CUSTOMERS), encoding="utf-8")
    return path


# Reading


def test_get_all_returns_every_customer(customer_file):
    assert CustomerRepository(customer_file).get_all() == SAMPLE_CUSTOMERS


def test_get_by_id_returns_matching_customer(customer_file):
    assert CustomerRepository(customer_file).get_by_id("cust_002")["name"] == "Ben"


def test_get_by_id_returns_none_for_unknown_id(customer_file):
    assert CustomerRepository(customer_file).get_by_id("cust_999") is None


def test_get_by_email_ignores_case_and_spaces(customer_file):
    found = CustomerRepository(customer_file).get_by_email("  ALICE@Example.com ")
    assert found["id"] == "cust_001"


def test_get_by_email_returns_none_for_unknown_email(customer_file):
    assert CustomerRepository(customer_file).get_by_email("nobody@example.com") is None


# Creating


def test_create_assigns_next_id_and_defaults(customer_file):
    new = CustomerRepository(customer_file).create(NEW_CUSTOMER)
    assert new["id"] == "cust_003"
    assert new["is_active"] is True
    assert new["role"] == "customer"
    assert new["addresses"] == []
    assert new["created_at"]


def test_create_ignores_id_sent_by_caller(customer_file):
    new = CustomerRepository(customer_file).create({**NEW_CUSTOMER, "id": "cust_001"})
    assert new["id"] == "cust_003"
    assert CustomerRepository(customer_file).get_by_id("cust_001")["name"] == "Alice"


def test_create_stores_email_lowercase(customer_file):
    new = CustomerRepository(customer_file).create(
        {**NEW_CUSTOMER, "email": "  Dana@Example.COM "}
    )
    assert new["email"] == "dana@example.com"


def test_created_record_matches_customer_model(customer_file):
    new = CustomerRepository(customer_file).create(NEW_CUSTOMER)
    customer = Customer(**new)
    assert "password_hash" not in CustomerPublic(**customer.model_dump()).model_dump()


def test_create_rejects_duplicate_email_and_changes_nothing(customer_file):
    before = customer_file.read_text(encoding="utf-8")
    with pytest.raises(DuplicateCustomerEmailError):
        CustomerRepository(customer_file).create(
            {**NEW_CUSTOMER, "email": "ALICE@example.com"}
        )
    assert customer_file.read_text(encoding="utf-8") == before


def test_created_customer_survives_restart(customer_file):
    CustomerRepository(customer_file).create(NEW_CUSTOMER)
    restarted = CustomerRepository(customer_file)
    assert restarted.get_by_email("dana@example.com")["id"] == "cust_003"
    assert len(restarted.get_all()) == 3


def test_create_never_reuses_an_id(tmp_path):
    path = tmp_path / "customers.json"
    records = [
        {**SAMPLE_CUSTOMERS[0], "id": "cust_001"},
        {**SAMPLE_CUSTOMERS[1], "id": "cust_007"},
    ]
    path.write_text(json.dumps(records), encoding="utf-8")
    assert CustomerRepository(path).create(NEW_CUSTOMER)["id"] == "cust_008"


# Updating and deactivating


def test_update_changes_only_given_fields(customer_file):
    updated = CustomerRepository(customer_file).update("cust_001", {"name": "Alice C"})
    assert updated["name"] == "Alice C"
    assert updated["email"] == "alice@example.com"
    assert CustomerRepository(customer_file).get_by_id("cust_001")["name"] == "Alice C"


def test_update_cannot_change_id_or_created_at(customer_file):
    updated = CustomerRepository(customer_file).update(
        "cust_001", {"id": "cust_999", "created_at": "1999-01-01", "name": "X"}
    )
    assert updated["id"] == "cust_001"
    assert updated["created_at"] == "2026-11-01T00:00:00+00:00"


def test_update_rejects_email_used_by_another_customer(customer_file):
    before = customer_file.read_text(encoding="utf-8")
    with pytest.raises(DuplicateCustomerEmailError):
        CustomerRepository(customer_file).update("cust_001", {"email": "BEN@example.com"})
    assert customer_file.read_text(encoding="utf-8") == before


def test_update_can_keep_own_email(customer_file):
    updated = CustomerRepository(customer_file).update(
        "cust_001", {"email": "Alice@Example.com"}
    )
    assert updated["email"] == "alice@example.com"


def test_update_unknown_id_returns_none_and_changes_nothing(customer_file):
    before = customer_file.read_text(encoding="utf-8")
    assert CustomerRepository(customer_file).update("cust_404", {"name": "Ghost"}) is None
    assert customer_file.read_text(encoding="utf-8") == before


def test_deactivate_keeps_record_but_marks_inactive(customer_file):
    CustomerRepository(customer_file).deactivate("cust_002")
    restarted = CustomerRepository(customer_file)
    customer = restarted.get_by_id("cust_002")
    assert customer is not None
    assert customer["is_active"] is False
    assert len(restarted.get_all()) == 2


def test_deactivate_unknown_id_returns_none(customer_file):
    assert CustomerRepository(customer_file).deactivate("cust_404") is None


# Invalid data files


def test_missing_file_raises(tmp_path):
    with pytest.raises(CustomerDataError, match="not found"):
        CustomerRepository(tmp_path / "nope.json").get_all()


def test_invalid_json_raises(tmp_path):
    path = tmp_path / "customers.json"
    path.write_text("{ not json", encoding="utf-8")
    with pytest.raises(CustomerDataError, match="Invalid JSON"):
        CustomerRepository(path).get_all()


def test_duplicate_ids_raise(tmp_path):
    path = tmp_path / "customers.json"
    duplicate = {**SAMPLE_CUSTOMERS[1], "id": "cust_001"}
    path.write_text(json.dumps([SAMPLE_CUSTOMERS[0], duplicate]), encoding="utf-8")
    with pytest.raises(CustomerDataError, match="Duplicate customer ID"):
        CustomerRepository(path).get_all()


def test_duplicate_emails_in_file_raise(tmp_path):
    path = tmp_path / "customers.json"
    clash = {**SAMPLE_CUSTOMERS[1], "email": "ALICE@example.com"}
    path.write_text(json.dumps([SAMPLE_CUSTOMERS[0], clash]), encoding="utf-8")
    with pytest.raises(CustomerDataError, match="Duplicate customer email"):
        CustomerRepository(path).get_all()


def test_customer_without_email_raises(tmp_path):
    path = tmp_path / "customers.json"
    path.write_text(json.dumps([{"id": "cust_001", "name": "No Email"}]), encoding="utf-8")
    with pytest.raises(CustomerDataError, match="email"):
        CustomerRepository(path).get_all()


# Committed representative data (read-only check)


def test_committed_seed_customers_are_valid():
    customers = CustomerRepository("data/customers.json").get_all()
    for record in customers:
        Customer(**record)
    assert any(not c["is_active"] for c in customers), "need a deactivated customer for the demo"