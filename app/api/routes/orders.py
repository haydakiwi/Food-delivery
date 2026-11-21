from fastapi import APIRouter, Depends, HTTPException, status

from app.api.dependencies.auth import CurrentCustomer, require_roles
from app.core.config import ORDERS_PATH
from app.repositories.order_repository import OrderRepository
from app.schemas.order import Order


router = APIRouter(
    prefix="/orders",
    tags=["Orders"],
    dependencies=[Depends(require_roles("customer"))],
)

order_repository = OrderRepository(ORDERS_PATH)


@router.get(
    "",
    response_model=list[Order],
    status_code=status.HTTP_200_OK,
    summary="Get order history",
    description=(
        "Return the authenticated customer's orders, newest first. "
        "Customers can only access their own order history."
    ),
)
def get_orders(customer: CurrentCustomer) -> list[Order]:
    return [
        Order(**order)
        for order in order_repository.get_by_customer(customer.id)
    ]


@router.get(
    "/{order_id}",
    response_model=Order,
    status_code=status.HTTP_200_OK,
    summary="Get one order",
    description=(
        "Return a single order belonging to the authenticated customer. "
        "An order that belongs to another customer is reported as not found, "
        "so the API never reveals which order IDs exist."
    ),
    responses={
        401: {"description": "Authentication required"},
        403: {"description": "Customer account is deactivated or not a customer"},
        404: {"description": "Order not found for this customer"},
    },
)
def get_order(order_id: str, customer: CurrentCustomer) -> Order:
    order = order_repository.get_by_id(order_id)

    if order is None or order["customer_id"] != customer.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order '{order_id}' was not found",
        )

    return Order(**order)