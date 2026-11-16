import json
from pathlib import Path

import pytest

from app.repositories.customer_repository import CustomerRepository
from app.services.auth_service import (
    AuthService,
    InactiveCustomerError,
    InvalidCredentialsError,
    InvalidTokenError,
    hash_password,
    verify_password,
)


def test_password_hash_is_salted_pbkdf2_and_verifies():
    first = hash_password("Password123!", iterations=1_000)
    second = hash_password("Password123!", iterations=1_000)

    assert first.startswith("pbkdf2_sha256$1000$")
    assert first != second
    assert "Password123!" not in first
    assert verify_password("Password123!", first)
    assert not verify_password("wrong", first)


def test_seed_password_matches_all_committed_seed_hashes():
    records = json.loads(Path("data/customers.json").read_text(encoding="utf-8"))
    assert records
    assert all(
        verify_password("Password123!", record["password_hash"])
        for record in records
    )


@pytest.fixture
def auth_repository(tmp_path: Path) -> CustomerRepository:
    records = json.loads(Path("data/customers.json").read_text(encoding="utf-8"))
    path = tmp_path / "customers.json"
    path.write_text(json.dumps(records), encoding="utf-8")
    return CustomerRepository(path)


def test_login_and_resolve_token_use_current_customer_state(auth_repository):
    auth = AuthService(auth_repository, "secret", clock=lambda: 100.0)

    response = auth.login("alice@example.com", "Password123!")

    assert response.customer.id == "cust_001"
    assert auth.resolve_token(response.access_token).email == "alice@example.com"


def test_wrong_password_is_rejected(auth_repository):
    auth = AuthService(auth_repository, "secret")
    with pytest.raises(InvalidCredentialsError):
        auth.login("alice@example.com", "wrong-password")


def test_deactivated_customer_cannot_login(auth_repository):
    auth = AuthService(auth_repository, "secret")
    with pytest.raises(InactiveCustomerError):
        auth.login("carla@example.com", "Password123!")


def test_token_tampering_and_expiration_are_rejected(auth_repository):
    now = [100.0]
    auth = AuthService(
        auth_repository, "secret", token_ttl_seconds=10, clock=lambda: now[0]
    )
    token = auth.login("alice@example.com", "Password123!").access_token

    with pytest.raises(InvalidTokenError):
        auth.resolve_token(token + "changed")

    with pytest.raises(InvalidTokenError):
        auth.resolve_token("payload.%")

    now[0] = 110.0
    with pytest.raises(InvalidTokenError):
        auth.resolve_token(token)


def test_deactivation_immediately_invalidates_existing_token(auth_repository):
    auth = AuthService(auth_repository, "secret")
    token = auth.login("alice@example.com", "Password123!").access_token
    auth_repository.deactivate("cust_001")

    with pytest.raises(InactiveCustomerError):
        auth.resolve_token(token)
