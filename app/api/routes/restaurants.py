from fastapi import APIRouter

from app.core.config import DATA_PATH
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.restaurant import Restaurant
from app.services.restaurant_service import RestaurantService


router = APIRouter()

repository = RestaurantRepository(DATA_PATH)
service = RestaurantService(repository)


@router.get("/restaurants", response_model=list[Restaurant])
def get_restaurants():
    return service.get_all_restaurants()