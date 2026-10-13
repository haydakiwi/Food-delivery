from pydantic import BaseModel

from app.schemas.menu_item import MenuItem


class Menu(BaseModel):
    """The customer-facing menu for one restaurant."""

    restaurant_id: str
    items: list[MenuItem]
