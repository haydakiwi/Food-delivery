"""Cart business rules, independent of HTTP routing."""

from app.repositories.cart_repository import (
    ActiveCartExistsError,
    CartNotActiveError,
    CartRepository,
)
from app.repositories.customer_repository import CustomerRepository
from app.repositories.menu_item_repository import MenuItemRepository
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.cart import Cart, CartItem
# from app.schemas.customer import Customer
# from app.schemas.menu_item import MenuItem


class CartCustomerNotFoundError(LookupError):
    """Raised when the customer does not exist."""


class InactiveCartCustomerError(ValueError):
    """Raised when an inactive customer tries to use a cart."""


class CartNotFoundError(LookupError):
    """Raised when the customer has no active cart."""


class CartOwnershipError(PermissionError):
    """Raised when a customer tries to access another customer's cart."""


class CartMenuItemNotFoundError(LookupError):
    """Raised when a menu item does not exist."""


class CartMenuItemUnavailableError(ValueError):
    """Raised when a menu item is unavailable."""


class CartRestaurantNotFoundError(LookupError):
    """Raised when a menu item's restaurant does not exist."""


class DifferentRestaurantError(ValueError):
    """Raised when a cart contains items from different restaurants."""


class CartItemNotFoundError(LookupError):
    """Raised when the requested item is not in the cart."""


class CartQuantityLimitError(ValueError):
    """Raised when the combined item quantity exceeds the maximum."""


class CartService:
    """Enforce cart rules using customer, restaurant, and menu repositories."""

    def __init__(
        self,
        cart_repository: CartRepository,
        customer_repository: CustomerRepository,
        restaurant_repository: RestaurantRepository,
        menu_item_repository: MenuItemRepository,
    ) -> None:
        self.cart_repository = cart_repository
        self.customer_repository = customer_repository
        self.restaurant_repository = restaurant_repository
        self.menu_item_repository = menu_item_repository

    def _validate_customer(self, customer_id: str) -> None:
        customer = self.customer_repository.get_by_id(customer_id)

        if customer is None:
            raise CartCustomerNotFoundError(customer_id)

        if not customer["is_active"]:
            raise InactiveCartCustomerError(customer_id)

    def _get_available_menu_item(self, menu_item_id: str) -> dict:
        item = self.menu_item_repository.get_by_id(menu_item_id)

        if item is None:
            raise CartMenuItemNotFoundError(menu_item_id)

        if not item["is_available"]:
            raise CartMenuItemUnavailableError(menu_item_id)

        restaurant = self.restaurant_repository.get_by_id(item["restaurant_id"])

        if restaurant is None:
            raise CartRestaurantNotFoundError(item["restaurant_id"])

        return item

    def get_active_cart(self, customer_id: str) -> Cart | None:
        """Return the customer's active cart, or None if they have no cart."""
        self._validate_customer(customer_id)

        cart = self.cart_repository.get_active_by_customer(customer_id)
        return Cart(**cart) if cart is not None else None

    def create_cart(self, customer_id: str) -> Cart:
        """Create an empty active cart for the customer."""
        self._validate_customer(customer_id)

        cart = self.cart_repository.create(customer_id)
        return Cart(**cart)

    def add_item(
        self,
        customer_id: str,
        menu_item_id: str,
        quantity: int = 1,
    ) -> Cart:
        """Add an available menu item, creating an active cart if necessary."""
        self._validate_customer(customer_id)

        # Validate the requested quantity before changing persistent data.
        requested_item = CartItem(
            menu_item_id=menu_item_id,
            quantity=quantity,
        )

        menu_item = self._get_available_menu_item(menu_item_id)
        cart_data = self.cart_repository.get_active_by_customer(customer_id)

        if cart_data is None:
            try:
                cart_data = self.cart_repository.create(customer_id)
            except ActiveCartExistsError:
                # Protect against another request creating the cart first.
                cart_data = self.cart_repository.get_active_by_customer(customer_id)
                if cart_data is None:
                    raise

        cart = Cart(**cart_data)
        restaurant_id = menu_item["restaurant_id"]

        if (
            cart.restaurant_id is not None
            and cart.restaurant_id != restaurant_id
        ):
            raise DifferentRestaurantError(
                "A cart can only contain items from one restaurant"
            )

        items = [item.model_dump() for item in cart.items]
        existing_item = next(
            (
                item
                for item in items
                if item["menu_item_id"] == requested_item.menu_item_id
            ),
            None,
        )

        if existing_item is not None:
            new_quantity = existing_item["quantity"] + requested_item.quantity

            if new_quantity > 50:
                raise CartQuantityLimitError(
                    "The total quantity of a menu item cannot exceed 50"
                )

            existing_item["quantity"] = new_quantity
        else:
            items.append(requested_item.model_dump())

        updated = self.cart_repository.update(
            cart.id,
            {
                "restaurant_id": restaurant_id,
                "items": items,
            },
        )

        return Cart(**updated)

    def update_item_quantity(
        self,
        customer_id: str,
        menu_item_id: str,
        quantity: int,
    ) -> Cart:
        """Set an existing cart item's quantity."""
        self._validate_customer(customer_id)

        requested_item = CartItem(
            menu_item_id=menu_item_id,
            quantity=quantity,
        )

        cart_data = self.cart_repository.get_active_by_customer(customer_id)
        if cart_data is None:
            raise CartNotFoundError(customer_id)

        cart = Cart(**cart_data)

        if not any(
            item.menu_item_id == requested_item.menu_item_id
            for item in cart.items
        ):
            raise CartItemNotFoundError(menu_item_id)

        menu_item = self._get_available_menu_item(menu_item_id)

        if menu_item["restaurant_id"] != cart.restaurant_id:
            raise DifferentRestaurantError(
                "The menu item does not belong to this cart's restaurant"
            )

        items = [item.model_dump() for item in cart.items]
        for item in items:
            if item["menu_item_id"] == menu_item_id:
                item["quantity"] = requested_item.quantity
                break

        updated = self.cart_repository.update(cart.id, {"items": items})
        return Cart(**updated)

    def remove_item(self, customer_id: str, menu_item_id: str) -> Cart:
        """Remove one item from the customer's active cart."""
        self._validate_customer(customer_id)

        cart_data = self.cart_repository.get_active_by_customer(customer_id)
        if cart_data is None:
            raise CartNotFoundError(customer_id)

        cart = Cart(**cart_data)
        items = [
            item.model_dump()
            for item in cart.items
            if item.menu_item_id != menu_item_id
        ]

        if len(items) == len(cart.items):
            raise CartItemNotFoundError(menu_item_id)

        changes = {"items": items}

        if not items:
            changes["restaurant_id"] = None

        updated = self.cart_repository.update(cart.id, changes)
        return Cart(**updated)

    def clear_cart(self, customer_id: str) -> Cart:
        """Remove all items from the customer's active cart."""
        self._validate_customer(customer_id)

        cart_data = self.cart_repository.get_active_by_customer(customer_id)
        if cart_data is None:
            raise CartNotFoundError(customer_id)

        updated = self.cart_repository.clear(cart_data["id"])
        return Cart(**updated)