from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.core.config import DATA_PATH, MENU_ITEMS_PATH
from app.repositories.menu_item_repository import MenuItemRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.restaurant import Restaurant
from app.services.restaurant_service import RestaurantService


router = APIRouter(prefix="/restaurants", tags=["Restaurants"])

restaurant_repository = RestaurantRepository(DATA_PATH)
menu_item_repository = MenuItemRepository(MENU_ITEMS_PATH)
service = RestaurantService(restaurant_repository, menu_item_repository)


@router.get("/restaurants", response_model=list[Restaurant])
def get_restaurants():
    return service.get_all_restaurants()