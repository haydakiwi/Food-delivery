from pydantic import BaseModel, Field


class Restaurant(BaseModel):
    id: str
    name: str
    cuisine: str
    rating: float
    delivery_time_minutes: int
    delivery_fee: float
    is_open: bool
    address: str


class RestaurantCreate(BaseModel):
    name: str = Field(min_length=1)
    cuisine: str = Field(min_length=1)
    rating: float = Field(ge=0, le=5)
    delivery_time_minutes: int = Field(gt=0)
    delivery_fee: float = Field(ge=0)
    is_open: bool = True
    address: str = Field(min_length=1)


class RestaurantUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1)
    cuisine: str | None = Field(default=None, min_length=1)
    rating: float | None = Field(default=None, ge=0, le=5)
    delivery_time_minutes: int | None = Field(default=None, gt=0)
    delivery_fee: float | None = Field(default=None, ge=0)
    is_open: bool | None = None
    address: str | None = Field(default=None, min_length=1)