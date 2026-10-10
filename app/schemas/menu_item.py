from pydantic import BaseModel, Field

class MenuItem(BaseModel):

    id: str
    restaurant_id: str
    name: str = Field(min_length = 1)
    description: str = ""
    price: float = Field(gt=0)
    category: str = Field(min_length = 1)
    is_available: bool = True

class MenuItemCreate(BaseModel):
    name: str = Field(min_length = 1)
    description: str = ""
    price: float = Field(gt=0)
    category: str = Field(min_length = 1)
    is_available: bool = True

class MenuItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length = 1)
    description: str | None = None
    price: float | None = Field(default=None, gt=0)
    category: str | None = Field(default=None, min_length = 1)
    is_available: bool | None = None
