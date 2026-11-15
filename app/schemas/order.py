from typing import Literal

from pydantic import BaseModel, Field, model_validator

from app.schemas.customer import DeliveryAddress

# M2 only creates orders. The full lifecycle (preparing, delivered, ...) is M3.
OrderStatus = Literal["placed"]

_HALF_CENT = 0.005


def _money(value: float) -> float:
    return round(value, 2)


class OrderItem(BaseModel):
    menu_item_id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    unit_price: float = Field(gt=0)
    quantity: int = Field(gt=0)
    line_total: float = Field(gt=0)

    @model_validator(mode="after")
    def check_line_total(self) -> "OrderItem":
        if abs(self.line_total - _money(self.unit_price * self.quantity)) > _HALF_CENT:
            raise ValueError("line_total must equal unit_price * quantity")
        return self


class OrderCreate(BaseModel):
    """What checkout passes to OrderRepository.create."""

    customer_id: str = Field(min_length=1)
    restaurant_id: str = Field(min_length=1)
    restaurant_name: str = Field(min_length=1)
    cart_id: str | None = None
    items: list[OrderItem] = Field(min_length=1)
    subtotal: float = Field(ge=0)
    delivery_fee: float = Field(ge=0)
    total: float = Field(ge=0)
    delivery_address: DeliveryAddress | None = None

    @model_validator(mode="after")
    def check_totals(self) -> "OrderCreate":
        expected_subtotal = _money(sum(item.line_total for item in self.items))
        if abs(self.subtotal - expected_subtotal) > _HALF_CENT:
            raise ValueError("subtotal must equal the sum of line totals")
        if abs(self.total - _money(self.subtotal + self.delivery_fee)) > _HALF_CENT:
            raise ValueError("total must equal subtotal + delivery_fee")
        return self


class Order(OrderCreate):
    """A stored order record (owned by OrderRepository)."""

    id: str
    status: OrderStatus = "placed"
    created_at: str