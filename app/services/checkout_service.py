
"""Checkout business rules, independent of HTTP routing."""

from pydantic import ValidationError

from app.repositories.cart_repository import (
    CartNotActiveError,
    CartRepository,
)
from app.repositories.customer_repository import CustomerRepository
from app.repositories.menu_item_repository import MenuItemRepository
from app.repositories.order_repository import (
    InvalidOrderError,
    OrderRepository,
)
from app.repositories.restaurant_repository import RestaurantRepository
from app.schemas.customer import DeliveryAddress
from app.schemas.order import Order, OrderCreate, OrderItem


class CheckoutCustomerNotFoundError(LookupError):
    """Raised when the customer does not exist."""


class InactiveCheckoutCustomerError(ValueError):
    """Raised when an inactive customer attempts checkout."""


class CheckoutCartNotFoundError(LookupError):
    """Raised when the customer has no active cart."""


class EmptyCheckoutCartError(ValueError):
    """Raised when the customer attempts to check out an empty cart."""


class CheckoutMenuItemNotFoundError(LookupError):
    """Raised when a cart menu item no longer exists."""


class CheckoutMenuItemUnavailableError(ValueError):
    """Raised when a cart menu item is no longer available."""


class CheckoutRestaurantNotFoundError(LookupError):
    """Raised when the cart's restaurant no longer exists."""


class CheckoutRestaurantMismatchError(ValueError):
    """Raised when a cart item belongs to a different restaurant."""


class CheckoutCartCloseError(RuntimeError):
    """Raised when the cart cannot be closed after an order is saved."""


class CheckoutService:
    """Validate carts and create orders using current menu and restaurant data."""

    def __init__(
        self,
        cart_repository: CartRepository,
        customer_repository: CustomerRepository,
        restaurant_repository: RestaurantRepository,
        menu_item_repository: MenuItemRepository,
        order_repository: OrderRepository,
    ) -> None:
        self.cart_repository = cart_repository
        self.customer_repository = customer_repository
        self.restaurant_repository = restaurant_repository
        self.menu_item_repository = menu_item_repository
        self.order_repository = order_repository

    def checkout(
        self,
        customer_id: str,
        delivery_address: DeliveryAddress | dict | None = None,
    ) -> Order:
        """Create an order from the customer's active cart.

        The order is saved before the cart is closed. This ensures a failed
        order save never leaves the customer's cart marked as checked out.
        """

        # Validate the customer.
        customer = self.customer_repository.get_by_id(customer_id)

        if customer is None:
            raise CheckoutCustomerNotFoundError(customer_id)

        if not customer["is_active"]:
            raise InactiveCheckoutCustomerError(customer_id)

        # Retrieve the customer's active cart.
        cart_data = self.cart_repository.get_active_by_customer(customer_id)

        if cart_data is None:
            raise CheckoutCartNotFoundError(customer_id)

        if not cart_data["items"]:
            raise EmptyCheckoutCartError("Cannot check out an empty cart")

        # Retrieve the current restaurant information.
        restaurant_id = cart_data["restaurant_id"]
        restaurant = self.restaurant_repository.get_by_id(restaurant_id)

        if restaurant is None:
            raise CheckoutRestaurantNotFoundError(restaurant_id)

        # Re-read every menu item so the order uses current prices and names.
        order_items = []

        for cart_item in cart_data["items"]:
            menu_item = self.menu_item_repository.get_by_id(
                cart_item["menu_item_id"]
            )

            if menu_item is None:
                raise CheckoutMenuItemNotFoundError(
                    cart_item["menu_item_id"]
                )

            if not menu_item["is_available"]:
                raise CheckoutMenuItemUnavailableError(
                    cart_item["menu_item_id"]
                )

            if menu_item["restaurant_id"] != restaurant_id:
                raise CheckoutRestaurantMismatchError(
                    "A cart item belongs to a different restaurant"
                )

            quantity = cart_item["quantity"]
            unit_price = round(float(menu_item["price"]), 2)

            order_items.append(
                OrderItem(
                    menu_item_id=menu_item["id"],
                    name=menu_item["name"],
                    unit_price=unit_price,
                    quantity=quantity,
                    line_total=round(unit_price * quantity, 2),
                )
            )

        # Calculate all prices on the server.
        subtotal = round(
            sum(item.line_total for item in order_items),
            2,
        )
        delivery_fee = round(float(restaurant["delivery_fee"]), 2)
        total = round(subtotal + delivery_fee, 2)

        # Validate and construct the order.
        try:
            order_data = OrderCreate(
                customer_id=customer_id,
                restaurant_id=restaurant_id,
                restaurant_name=restaurant["name"],
                cart_id=cart_data["id"],
                items=order_items,
                subtotal=subtotal,
                delivery_fee=delivery_fee,
                total=total,
                delivery_address=delivery_address,
            )
        except ValidationError as exc:
            raise InvalidOrderError(str(exc)) from exc

        # Save the order BEFORE closing the cart.
        saved_order = self.order_repository.create(order_data)

        # Close the cart only after the order has been saved successfully.
        try:
            closed_cart = self.cart_repository.close(
                cart_data["id"],
                status="checked_out",
            )
        except CartNotActiveError as exc:
            raise CheckoutCartCloseError(
                "The order was saved, but the cart could not be closed"
            ) from exc

        if closed_cart is None:
            raise CheckoutCartCloseError(
                "The order was saved, but the cart could not be found to close"
            )

        return Order(**saved_order)
