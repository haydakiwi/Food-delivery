from typing import Annotated

from fastapi import APIRouter, HTTPException, Path, Query, status

from app.core.config import DATA_PATH, MENU_ITEMS_PATH
from app.repositories.menu_item_repository import MenuItemRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.menu import Menu
from app.schemas.menu_item import MenuItem
from app.schemas.restaurant import Restaurant
from app.services.restaurant_service import (
    MenuItemNotFoundError,
    RestaurantNotFoundError,
    RestaurantService,
)


router = APIRouter(prefix="/restaurants", tags=["Restaurants"])

restaurant_repository = RestaurantRepository(DATA_PATH)
menu_item_repository = MenuItemRepository(MENU_ITEMS_PATH)
service = RestaurantService(restaurant_repository, menu_item_repository)


@router.get(
    "",
    response_model=list[Restaurant],
    status_code=status.HTTP_200_OK,
    summary="List restaurants",
    description=(
        "Return all restaurants, optionally filtered by a case-insensitive name "
        "search, cuisine, and open status."
    ),
)
def get_restaurants(
    search: Annotated[
        str | None,
        Query(description="Case-insensitive text to find in a restaurant name"),
    ] = None,
    cuisine: Annotated[
        str | None,
        Query(description="Case-insensitive exact cuisine filter"),
    ] = None,
    is_open: Annotated[
        bool | None,
        Query(description="Filter by whether the restaurant is currently open"),
    ] = None,
) -> list[Restaurant]:
    return service.get_all_restaurants(
        search=search,
        cuisine=cuisine,
        is_open=is_open,
    )


@router.get(
    "/{restaurant_id}",
    response_model=Restaurant,
    status_code=status.HTTP_200_OK,
    summary="Get restaurant details",
    description="Return the details of one restaurant using its stable identifier.",
    responses={404: {"description": "Restaurant not found"}},
)
def get_restaurant(
    restaurant_id: Annotated[
        str,
        Path(description="Stable restaurant identifier", examples=["rest_001"]),
    ],
) -> Restaurant:
    try:
        return service.get_restaurant(restaurant_id)
    except RestaurantNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant '{restaurant_id}' not found",
        ) from exc


@router.get(
    "/{restaurant_id}/menu",
    response_model=Menu,
    status_code=status.HTTP_200_OK,
    summary="Get a restaurant menu",
    description="Return all menu items belonging to the selected restaurant.",
    responses={404: {"description": "Restaurant not found"}},
)
def get_restaurant_menu(
    restaurant_id: Annotated[
        str,
        Path(description="Stable restaurant identifier", examples=["rest_001"]),
    ],
) -> Menu:
    try:
        return service.get_menu(restaurant_id)
    except RestaurantNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant '{restaurant_id}' not found",
        ) from exc


@router.get(
    "/{restaurant_id}/menu/items/{item_id}",
    response_model=MenuItem,
    status_code=status.HTTP_200_OK,
    summary="Get a menu item",
    description="Return one menu item belonging to the selected restaurant.",
    responses={
        404: {"description": "Restaurant or menu item not found"},
    },
)
def get_restaurant_menu_item(
    restaurant_id: Annotated[
        str,
        Path(description="Stable restaurant identifier", examples=["rest_001"]),
    ],
    item_id: Annotated[
        str,
        Path(description="Stable menu-item identifier", examples=["item_001"]),
    ],
) -> MenuItem:
    try:
        return service.get_menu_item(restaurant_id, item_id)
    except RestaurantNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Restaurant '{restaurant_id}' not found",
        ) from exc
    except MenuItemNotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(
                f"Menu item '{item_id}' was not found for restaurant "
                f"'{restaurant_id}'"
            ),
        ) from exc
