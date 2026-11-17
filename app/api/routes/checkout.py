from fastapi import APIRouter, Body, Depends, HTTPException, status

from app.api.dependencies.auth import CurrentCustomer, require_roles
from app.core.config import (
    CARTS_PATH,
    CUSTOMERS_PATH,
    DATA_PATH,
    MENU_ITEMS_PATH,
    ORDERS_PATH,
)
from app.repositories.cart_repository import CartRepository
from app.repositories.customer_repository import CustomerRepository
from app.repositories.menu_item_repository import MenuItemRepository
from app.repositories.order_repository import InvalidOrderError, OrderRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.customer import DeliveryAddress
from app.schemas.order import Order
from app.services.checkout_service import (
    CheckoutCartCloseError,
    CheckoutCartNotFoundError,
    CheckoutCustomerNotFoundError,
    CheckoutMenuItemNotFoundError,
    CheckoutMenuItemUnavailableError,
    CheckoutRestaurantMismatchError,
    CheckoutRestaurantNotFoundError,
    CheckoutService,
    EmptyCheckoutCartError,
    InactiveCheckoutCustomerError,
)


router = APIRouter(
    prefix="/checkout",
    tags=["Checkout"],
    dependencies=[Depends(require_roles("customer"))],
)

cart_repository = CartRepository(CARTS_PATH)
customer_repository = CustomerRepository(CUSTOMERS_PATH)
restaurant_repository = RestaurantRepository(DATA_PATH)
menu_item_repository = MenuItemRepository(MENU_ITEMS_PATH)
order_repository = OrderRepository(ORDERS_PATH)

service = CheckoutService(
    cart_repository,
    customer_repository,
    restaurant_repository,
    menu_item_repository,
    order_repository,
)


@router.post(
    "",
    response_model=Order,
    status_code=status.HTTP_201_CREATED,
    summary="Checkout cart",
    description=(
        "Create an order from the authenticated customer's active cart. "
        "Prices and delivery fees are calculated using current server data."
    ),
    responses={
        403: {"description": "Customer account is inactive"},
        404: {"description": "Cart, customer, restaurant, or menu item not found"},
        409: {"description": "Cart is empty or checkout validation failed"},
        422: {"description": "Invalid order data"},
        500: {"description": "Order saved but cart could not be closed"},
    },
)
def checkout(
    customer: CurrentCustomer,
    delivery_address: DeliveryAddress | None = Body(default=None),
) -> Order:
    try:
        return service.checkout(customer.id, delivery_address)
    except InactiveCheckoutCustomerError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account is inactive",
        ) from exc
    except (
        CheckoutCustomerNotFoundError,
        CheckoutCartNotFoundError,
        CheckoutMenuItemNotFoundError,
        CheckoutRestaurantNotFoundError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    except (
        EmptyCheckoutCartError,
        CheckoutMenuItemUnavailableError,
        CheckoutRestaurantMismatchError,
    ) as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except InvalidOrderError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except CheckoutCartCloseError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc
