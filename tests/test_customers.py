import json
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.services.auth_service import verify_password


@pytest.fixture
def customers_data_file(tmp_path: Path) -> Path:
    records = json.loads(Path("data/customers.json").read_text(encoding="utf-8"))
    path = tmp_path / "customers.json"
    path.write_text(json.dumps(records), encoding="utf-8")
    return path


@pytest.fixture
def customer_client(
    client_factory: Callable[..., TestClient],
    restaurant_data_file: Path,
    menu_items_data_file: Path,
    customers_data_file: Path,
) -> TestClient:
    return client_factory(
        restaurant_data_file, menu_items_data_file, customers_data_file
    )


def _login(
    client: TestClient,
    email: str = "alice@example.com",
    password: str = "Password123!",
) -> str:
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()["access_token"]


def _authorization(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_registration_hashes_password_and_never_exposes_hash(
    customer_client: TestClient, customers_data_file: Path
):
    response = customer_client.post(
        "/customers/register",
        json={
            "name": "Dana",
            "email": " Dana@Example.com ",
            "password": "StrongPass123!",
            "phone": "250-555-0100",
        },
    )

    assert response.status_code == 201
    assert response.json()["email"] == "dana@example.com"
    assert "password_hash" not in response.json()
    stored = json.loads(customers_data_file.read_text(encoding="utf-8"))[-1]
    assert "password" not in stored
    assert stored["password_hash"] != "StrongPass123!"
    assert verify_password("StrongPass123!", stored["password_hash"])


def test_duplicate_registration_returns_409_without_changing_data(
    customer_client: TestClient, customers_data_file: Path
):
    before = customers_data_file.read_text(encoding="utf-8")
    response = customer_client.post(
        "/customers/register",
        json={
            "name": "Duplicate",
            "email": "ALICE@example.com",
            "password": "Password123!",
        },
    )
    assert response.status_code == 409
    assert customers_data_file.read_text(encoding="utf-8") == before


def test_login_returns_bearer_token_and_public_customer(customer_client: TestClient):
    response = customer_client.post(
        "/auth/login",
        json={"email": "ALICE@example.com", "password": "Password123!"},
    )
    body = response.json()

    assert response.status_code == 200
    assert body["token_type"] == "bearer"
    assert body["access_token"]
    assert body["customer"]["id"] == "cust_001"
    assert "password_hash" not in body["customer"]


def test_wrong_password_and_deactivated_customer_are_rejected(
    customer_client: TestClient,
):
    wrong_password = customer_client.post(
        "/auth/login",
        json={"email": "alice@example.com", "password": "not-the-password"},
    )
    inactive = customer_client.post(
        "/auth/login",
        json={"email": "carla@example.com", "password": "Password123!"},
    )

    assert wrong_password.status_code == 401
    assert inactive.status_code == 403


def test_profile_requires_valid_authentication(customer_client: TestClient):
    assert customer_client.get("/customers/me").status_code == 401
    assert (
        customer_client.get(
            "/customers/me", headers=_authorization("not-a-token")
        ).status_code
        == 401
    )


def test_customer_can_update_profile_addresses_and_deactivate(
    customer_client: TestClient, customers_data_file: Path
):
    token = _login(customer_client)
    headers = _authorization(token)
    update = customer_client.patch(
        "/customers/me",
        headers=headers,
        json={
            "name": "Alice Updated",
            "phone": "250-555-0199",
            "addresses": [
                {
                    "label": "Home",
                    "street": "1 Main St",
                    "city": "Kelowna",
                    "province": "BC",
                    "postal_code": "V1V 1V1",
                    "is_default": True,
                }
            ],
        },
    )
    deactivated = customer_client.post(
        "/customers/me/deactivate", headers=headers
    )

    assert update.status_code == 200
    assert update.json()["addresses"][0]["city"] == "Kelowna"
    assert deactivated.status_code == 200
    assert deactivated.json()["is_active"] is False
    assert customer_client.get("/customers/me", headers=headers).status_code == 403
    stored = json.loads(customers_data_file.read_text(encoding="utf-8"))[0]
    assert stored["name"] == "Alice Updated"
    assert stored["is_active"] is False


def test_update_to_taken_email_returns_409(customer_client: TestClient):
    token = _login(customer_client)
    response = customer_client.patch(
        "/customers/me",
        headers=_authorization(token),
        json={"email": "ben@example.com"},
    )
    assert response.status_code == 409


def test_admin_lookup_enforces_role_and_returns_public_customer(
    customer_client: TestClient,
):
    customer_token = _login(customer_client)
    forbidden = customer_client.get(
        "/customers/cust_002", headers=_authorization(customer_token)
    )
    admin_token = _login(customer_client, "admin@example.com")
    allowed = customer_client.get(
        "/customers/cust_002", headers=_authorization(admin_token)
    )
    missing = customer_client.get(
        "/customers/cust_999", headers=_authorization(admin_token)
    )

    assert forbidden.status_code == 403
    assert allowed.status_code == 200
    assert allowed.json()["id"] == "cust_002"
    assert "password_hash" not in allowed.json()
    assert missing.status_code == 404


def test_integrated_registration_login_profile_and_menu_flow(
    customer_client: TestClient,
):
    registration = customer_client.post(
        "/customers/register",
        json={
            "name": "Integrated User",
            "email": "integrated@example.com",
            "password": "Password123!",
        },
    )
    token = _login(customer_client, "integrated@example.com")
    profile = customer_client.get(
        "/customers/me", headers=_authorization(token)
    )
    menu = customer_client.get("/restaurants/1/menu")

    assert registration.status_code == 201
    assert profile.status_code == 200
    assert profile.json()["email"] == "integrated@example.com"
    assert menu.status_code == 200
    assert menu.json()["items"]


def test_openapi_documents_customer_auth_without_password_hash_response(
    customer_client: TestClient,
):
    schema = customer_client.get("/openapi.json").json()

    assert "/customers/register" in schema["paths"]
    assert "/auth/login" in schema["paths"]
    assert "password_hash" not in schema["components"]["schemas"]["CustomerPublic"][
        "properties"
    ]
