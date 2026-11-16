"""Password hashing and signed bearer-token authentication."""

from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import secrets
import time
from collections.abc import Callable

from app.repositories.customer_repository import CustomerRepository
from app.schemas.auth import TokenResponse
from app.schemas.customer import Customer, CustomerPublic


class InvalidCredentialsError(ValueError):
    """Raised when an email/password pair cannot be authenticated."""


class InvalidTokenError(ValueError):
    """Raised when a bearer token is malformed, changed, or expired."""


class InactiveCustomerError(PermissionError):
    """Raised when a deactivated customer tries a protected operation."""


def hash_password(password: str, iterations: int = 100_000) -> str:
    """Return a salted PBKDF2-SHA256 hash compatible with seeded customers."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return f"pbkdf2_sha256${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, encoded_hash: str) -> bool:
    """Safely verify a password without exposing or storing the plaintext."""
    try:
        algorithm, raw_iterations, salt_hex, expected_hex = encoded_hash.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        iterations = int(raw_iterations)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(expected_hex)
    except (TypeError, ValueError):
        return False

    actual = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, iterations
    )
    return hmac.compare_digest(actual, expected)


def _base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding)


class AuthService:
    """Authenticates credentials and resolves signed tokens to current customers."""

    def __init__(
        self,
        customer_repository: CustomerRepository,
        secret: str,
        token_ttl_seconds: int = 3600,
        clock: Callable[[], float] = time.time,
    ) -> None:
        if not secret:
            raise ValueError("AUTH_SECRET must not be empty")
        if token_ttl_seconds <= 0:
            raise ValueError("AUTH_TOKEN_TTL_SECONDS must be positive")
        self.customer_repository = customer_repository
        self._secret = secret.encode("utf-8")
        self.token_ttl_seconds = token_ttl_seconds
        self._clock = clock

    def login(self, email: str, password: str) -> TokenResponse:
        record = self.customer_repository.get_by_email(email)
        if record is None or not verify_password(password, record["password_hash"]):
            raise InvalidCredentialsError()
        customer = Customer(**record)
        if not customer.is_active:
            raise InactiveCustomerError(customer.id)

        token = self._issue_token(customer.id)
        return TokenResponse(
            access_token=token,
            expires_in=self.token_ttl_seconds,
            customer=CustomerPublic(**customer.model_dump()),
        )

    def resolve_token(self, token: str) -> CustomerPublic:
        customer_id = self._read_subject(token)
        record = self.customer_repository.get_by_id(customer_id)
        if record is None:
            raise InvalidTokenError()
        customer = Customer(**record)
        if not customer.is_active:
            raise InactiveCustomerError(customer.id)
        return CustomerPublic(**customer.model_dump())

    def _issue_token(self, customer_id: str) -> str:
        issued_at = int(self._clock())
        payload = json.dumps(
            {
                "sub": customer_id,
                "iat": issued_at,
                "exp": issued_at + self.token_ttl_seconds,
            },
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        encoded_payload = _base64url_encode(payload)
        signature = hmac.new(
            self._secret, encoded_payload.encode("ascii"), hashlib.sha256
        ).digest()
        return f"{encoded_payload}.{_base64url_encode(signature)}"

    def _read_subject(self, token: str) -> str:
        try:
            encoded_payload, encoded_signature = token.split(".", 1)
            supplied_signature = _base64url_decode(encoded_signature)
            expected_signature = hmac.new(
                self._secret, encoded_payload.encode("ascii"), hashlib.sha256
            ).digest()
            if not hmac.compare_digest(supplied_signature, expected_signature):
                raise InvalidTokenError()
            payload = json.loads(_base64url_decode(encoded_payload))
            subject = payload["sub"]
            expires_at = int(payload["exp"])
            if not isinstance(subject, str) or expires_at <= int(self._clock()):
                raise InvalidTokenError()
            return subject
        except InvalidTokenError:
            raise
        except (
            binascii.Error,
            KeyError,
            TypeError,
            ValueError,
            json.JSONDecodeError,
        ) as exc:
            raise InvalidTokenError() from exc
