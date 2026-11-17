from fastapi import APIRouter, Depends, status

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
