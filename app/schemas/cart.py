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