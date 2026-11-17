"""Shared authentication and role-authorization dependencies."""

from collections.abc import Callable
from functools import partial
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import (
    AUTH_SECRET,
    AUTH_TOKEN_TTL_SECONDS,
    CUSTOMERS_PATH,
    PASSWORD_HASH_ITERATIONS,
)
from app.repositories.customer_repository import CustomerRepository
from app.schemas.customer import CustomerPublic, CustomerRole
from app.services.auth_service import (
    AuthService,
    InactiveCustomerError,
    InvalidTokenError,
    hash_password,
)
from app.services.customer_service import CustomerService


customer_repository = CustomerRepository(CUSTOMERS_PATH)
customer_service = CustomerService(
    customer_repository,
    password_hasher=partial(
        hash_password, iterations=PASSWORD_HASH_ITERATIONS
    ),
)
auth_service = AuthService(
    customer_repository,
    secret=AUTH_SECRET,
    token_ttl_seconds=AUTH_TOKEN_TTL_SECONDS,
)
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_customer(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None, Depends(bearer_scheme)
    ],
) -> CustomerPublic:
    """Return the active customer represented by the current bearer token."""
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        return auth_service.resolve_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InactiveCustomerError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account is deactivated",
        ) from exc


CurrentCustomer = Annotated[CustomerPublic, Depends(get_current_customer)]


def require_roles(
    *allowed_roles: CustomerRole,
) -> Callable[[CurrentCustomer], CustomerPublic]:
    """Build a dependency that permits only the supplied backend roles."""

    def check_role(customer: CurrentCustomer) -> CustomerPublic:
        if customer.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return customer

    return check_role
