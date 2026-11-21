from typing import Literal

from pydantic import BaseModel, Field, model_validator

MAX_ITEM_QUANTITY = 50

CartStatus = Literal["active", "checked_out", "abandoned"]


class CartItem(BaseModel):
    menu_item_id: str = Field(min_length=1)
    quantity: int = Field(gt=0, le=MAX_ITEM_QUANTITY)


class Cart(BaseModel):
    """A stored cart record (owned by CartRepository)."""

    id: str
    customer_id: str = Field(min_length=1)
    restaurant_id: str | None = None
    items: list[CartItem] = Field(default_factory=list)
    status: CartStatus = "active"
    created_at: str
    updated_at: str

    @model_validator(mode="after")
    def check_items(self) -> "Cart":
        ids = [item.menu_item_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("a menu item may appear only once in a cart")
        if self.items and self.restaurant_id is None:
            raise ValueError("a cart with items must have a restaurant_id")
        return self


class CartItemAdd(BaseModel):
    """Request body for adding an item to the cart."""

    menu_item_id: str = Field(min_length=1)
    quantity: int = Field(default=1, gt=0, le=MAX_ITEM_QUANTITY)


class CartItemQuantityUpdate(BaseModel):
    """Request body for changing an item's quantity."""

    quantity: int = Field(gt=0, le=MAX_ITEM_QUANTITY)


class CartResponse(Cart):
    """Cart returned by the API, including server-calculated totals."""

    subtotal: float = Field(ge=0)
    delivery_fee: float = Field(ge=0)
    total: float = Field(ge=0)

    @model_validator(mode="after")
    def check_totals(self) -> "CartResponse":
        expected_total = round(self.subtotal + self.delivery_fee, 2)

        if round(self.total, 2) != expected_total:
            raise ValueError("total must equal subtotal + delivery_fee")

        return self