from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import (
    CurrentCustomer,
    auth_service,
    customer_service,
    require_roles,
)
from app.repositories.customer_repository import DuplicateCustomerEmailError
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.customer import CustomerCreate, CustomerPublic, CustomerUpdate
from app.services.auth_service import InactiveCustomerError, InvalidCredentialsError
from app.services.customer_service import CustomerNotFoundError


router = APIRouter(tags=["Customers and authentication"])


@router.post(
    "/customers/register",
    response_model=CustomerPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Register a customer",
    responses={409: {"description": "Email address is already registered"}},
)
def register_customer(data: CustomerCreate) -> CustomerPublic:
    try:
        return customer_service.register(data)
    except DuplicateCustomerEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address is already registered",
        ) from exc


@router.post(
    "/auth/login",
    response_model=TokenResponse,
    summary="Sign in",
    responses={
        401: {"description": "Email or password is incorrect"},
        403: {"description": "Customer account is deactivated"},
    },
)
def login(data: LoginRequest) -> TokenResponse:
    try:
        return auth_service.login(data.email, data.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InactiveCustomerError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account is deactivated",
        ) from exc


@router.get(
    "/customers/me",
    response_model=CustomerPublic,
    summary="Get my customer profile",
)
def get_my_profile(customer: CurrentCustomer) -> CustomerPublic:
    return customer


@router.patch(
    "/customers/me",
    response_model=CustomerPublic,
    summary="Update my customer profile",
    responses={409: {"description": "Email address is already registered"}},
)
def update_my_profile(
    data: CustomerUpdate, customer: CurrentCustomer
) -> CustomerPublic:
    try:
        return customer_service.update_customer(customer.id, data)
    except DuplicateCustomerEmailError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email address is already registered",
        ) from exc


@router.post(
    "/customers/me/deactivate",
    response_model=CustomerPublic,
    summary="Deactivate my customer account",
)
def deactivate_my_account(customer: CurrentCustomer) -> CustomerPublic:
    return customer_service.deactivate_customer(customer.id)


@router.get(
    "/customers/{customer_id}",
    response_model=CustomerPublic,
    summary="Get a customer as an administrator",
    responses={
        403: {"description": "Administrator role required"},
        404: {"description": "Customer not found"},
    },
)
def get_customer_as_admin(
    customer_id: str,
    _admin: Annotated[CustomerPublic, Depends(require_roles("admin"))],
) -> CustomerPublic:
    try:
        return customer_service.get_customer(customer_id)
    except CustomerNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer '{customer_id}' not found",
        ) from exc
