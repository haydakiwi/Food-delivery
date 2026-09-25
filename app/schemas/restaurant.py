from pydantic import BaseModel


class Restaurant(BaseModel):
    id: str
    name: str
    cuisine: str
    rating: float
    delivery_time_minutes: int
    delivery_fee: float
    is_open: bool
    address: str