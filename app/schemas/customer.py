
from typing import Literal

from pydantic import BaseModel, Field, field_validator

EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

CustomerRole = Literal["customer", "restaurant_owner", "admin"]


def normalize_email(email: str) -> str:
    """Store emails trimmed and lower-case so lookups are consistent."""
    return email.strip().casefold()


class DeliveryAddress(BaseModel):
    label: str = Field(default="Home", min_length=1)
    street: str = Field(min_length=1)
    city: str = Field(min_length=1)
    province: str = Field(min_length=1)
    postal_code: str = Field(min_length=1)
    is_default: bool = False


class Customer(BaseModel):
    """A stored customer record (owned by CustomerRepository)."""

    id: str
    name: str = Field(min_length=1)
    email: str = Field(pattern=EMAIL_PATTERN)
    phone: str | None = None
    password_hash: str = Field(min_length=1)
    role: CustomerRole = "customer"
    is_active: bool = True
    addresses: list[DeliveryAddress] = Field(default_factory=list)
    created_at: str

    @field_validator("email", mode="before")
    @classmethod
    def _normalize(cls, value: object) -> object:
        return normalize_email(value) if isinstance(value, str) else value


class CustomerPublic(BaseModel):
    """Customer data that is safe to return from the API (no password hash)."""

    id: str
    name: str
    email: str
    phone: str | None = None
    role: CustomerRole
    is_active: bool
    addresses: list[DeliveryAddress]
    created_at: str


class CustomerCreate(BaseModel):
    """Registration request. The auth service hashes password before saving."""

    name: str = Field(min_length=1)
    email: str = Field(pattern=EMAIL_PATTERN)
    password: str = Field(min_length=8)
    phone: str | None = None
    addresses: list[DeliveryAddress] = Field(default_factory=list)


class CustomerUpdate(BaseModel):
    """Fields a customer may change on their own account."""

    name: str | None = Field(default=None, min_length=1)
    email: str | None = Field(default=None, pattern=EMAIL_PATTERN)
    phone: str | None = None
    addresses: list[DeliveryAddress] | None = None