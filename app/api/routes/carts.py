
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import CurrentCustomer, require_roles
from app.core.config import (
    CARTS_PATH,
    CUSTOMERS_PATH,
    DATA_PATH,
    MENU_ITEMS_PATH,
)
from app.repositories.cart_repository import (
    ActiveCartExistsError,
    CartNotActiveError,
    CartRepository,
)
from app.repositories.customer_repository import CustomerRepository
from app.repositories.menu_item_repository import MenuItemRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.cart import CartResponse, CartItemAdd, CartItemQuantityUpdate
from app.services.cart_service import (
    CartCustomerNotFoundError,
    CartItemNotFoundError,
    CartMenuItemNotFoundError,
    CartMenuItemUnavailableError,
    CartNotFoundError,
    CartQuantityLimitError,
    CartService,
    DifferentRestaurantError,
    InactiveCartCustomerError,
)


router = APIRouter(
    prefix="/carts",
    tags=["Carts"],
    dependencies=[Depends(require_roles("customer"))],
)

cart_repository = CartRepository(CARTS_PATH)
customer_repository = CustomerRepository(CUSTOMERS_PATH)
restaurant_repository = RestaurantRepository(DATA_PATH)
menu_item_repository = MenuItemRepository(MENU_ITEMS_PATH)

service = CartService(
    cart_repository,
    customer_repository,
    restaurant_repository,
    menu_item_repository,
)


def _raise_cart_error(exc: Exception) -> None:
    """Translate cart service and repository exceptions into HTTP responses."""

    if isinstance(exc, InactiveCartCustomerError):
        code = status.HTTP_403_FORBIDDEN
        detail = "Customer account is inactive"
    elif isinstance(
        exc,
        (
            CartCustomerNotFoundError,
            CartNotFoundError,
            CartMenuItemNotFoundError,
            CartItemNotFoundError,
        ),
    ):
        code = status.HTTP_404_NOT_FOUND
        detail = str(exc)
    elif isinstance(exc, CartMenuItemUnavailableError):
        code = status.HTTP_409_CONFLICT
        detail = "Menu item is currently unavailable"
    elif isinstance(
        exc,
        (
            DifferentRestaurantError,
            CartQuantityLimitError,
            ActiveCartExistsError,
            CartNotActiveError,
        ),
    ):
        code = status.HTTP_409_CONFLICT
        detail = str(exc)
    else:
        raise exc

    raise HTTPException(status_code=code, detail=detail) from exc


@router.get(
    "",
    response_model=CartResponse | None,
    status_code=status.HTTP_200_OK,
    summary="Get active cart",
    description="Return the authenticated customer's active cart, if one exists.",
)
def get_cart(customer: CurrentCustomer) -> CartResponse | None:
    try:
        return service.get_active_cart(customer.id)
    except (
        CartCustomerNotFoundError,
        InactiveCartCustomerError,
    ) as exc:
        _raise_cart_error(exc)


@router.post(
    "",
    response_model=CartResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create cart",
    description="Create an empty active cart for the authenticated customer.",
    responses={409: {"description": "An active cart already exists"}},
)
def create_cart(customer: CurrentCustomer) -> CartResponse:
    try:
        return service.create_cart(customer.id)
    except (
        CartCustomerNotFoundError,
        InactiveCartCustomerError,
        ActiveCartExistsError,
    ) as exc:
        _raise_cart_error(exc)


@router.post(
    "/items",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="Add item to cart",
    description=(
        "Add an available menu item to the authenticated customer's cart. "
        "An active cart is created automatically if necessary."
    ),
    responses={
        404: {"description": "Customer or menu item not found"},
        409: {"description": "Item unavailable or cart rule violated"},
        422: {"description": "Invalid item or quantity"},
    },
)
def add_cart_item(
    data: CartItemAdd,
    customer: CurrentCustomer,
) -> Cart:
    try:
        return service.add_item(
            customer.id,
            data.menu_item_id,
            data.quantity,
        )
    except (
        CartCustomerNotFoundError,
        InactiveCartCustomerError,
        CartMenuItemNotFoundError,
        CartMenuItemUnavailableError,
        DifferentRestaurantError,
        CartQuantityLimitError,
        ActiveCartExistsError,
    ) as exc:
        _raise_cart_error(exc)


@router.patch(
    "/items/{menu_item_id}",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="Update cart item quantity",
    description="Set the quantity of an existing item in the active cart.",
    responses={
        404: {"description": "Cart or menu item not found"},
        409: {"description": "Item unavailable or cart rule violated"},
        422: {"description": "Invalid quantity"},
    },
)
def update_cart_item(
    menu_item_id: str,
    data: CartItemQuantityUpdate,
    customer: CurrentCustomer,
) -> Cart:
    try:
        return service.update_item_quantity(
            customer.id,
            menu_item_id,
            data.quantity,
        )
    except (
        CartCustomerNotFoundError,
        InactiveCartCustomerError,
        CartNotFoundError,
        CartItemNotFoundError,
        CartMenuItemNotFoundError,
        CartMenuItemUnavailableError,
        DifferentRestaurantError,
    ) as exc:
        _raise_cart_error(exc)


@router.delete(
    "/items/{menu_item_id}",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove cart item",
    description="Remove one item from the authenticated customer's active cart.",
    responses={404: {"description": "Cart or item not found"}},
)
def remove_cart_item(
    menu_item_id: str,
    customer: CurrentCustomer,
) -> Cart:
    try:
        return service.remove_item(customer.id, menu_item_id)
    except (
        CartCustomerNotFoundError,
        InactiveCartCustomerError,
        CartNotFoundError,
        CartItemNotFoundError,
    ) as exc:
        _raise_cart_error(exc)


@router.delete(
    "/items",
    response_model=CartResponse,
    status_code=status.HTTP_200_OK,
    summary="Clear cart",
    description="Remove all items from the authenticated customer's active cart.",
    responses={404: {"description": "Active cart not found"}},
)
def clear_cart(customer: CurrentCustomer) -> Cart:
    try:
        return service.clear_cart(customer.id)
    except (
        CartCustomerNotFoundError,
        InactiveCartCustomerError,
        CartNotFoundError,
    ) as exc:
        _raise_cart_error(exc)
