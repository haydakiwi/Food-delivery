from typing import Any

Records = list[dict[str, Any]]


def find_relationship_problems(
    customers: Records,
    restaurants: Records,
    menu_items: Records,
    carts: Records,
    orders: Records,
) -> list[str]:
    """Return a human-readable list of broken references (empty if all valid)."""
    problems: list[str] = []
    customer_ids = {c["id"] for c in customers}
    restaurant_ids = {r["id"] for r in restaurants}
    item_restaurant = {m["id"]: m["restaurant_id"] for m in menu_items}
    cart_ids = {c["id"] for c in carts}

    for item in menu_items:
        if item["restaurant_id"] not in restaurant_ids:
            problems.append(
                f"Menu item {item['id']} references unknown restaurant {item['restaurant_id']}"
            )

    for cart in carts:
        if cart["customer_id"] not in customer_ids:
            problems.append(
                f"Cart {cart['id']} references unknown customer {cart['customer_id']}"
            )
        restaurant_id = cart.get("restaurant_id")
        if restaurant_id is not None and restaurant_id not in restaurant_ids:
            problems.append(f"Cart {cart['id']} references unknown restaurant {restaurant_id}")
        for line in cart.get("items", []):
            problems.extend(
                _check_item(f"Cart {cart['id']}", line["menu_item_id"], restaurant_id, item_restaurant)
            )

    for order in orders:
        if order["customer_id"] not in customer_ids:
            problems.append(
                f"Order {order['id']} references unknown customer {order['customer_id']}"
            )
        if order["restaurant_id"] not in restaurant_ids:
            problems.append(
                f"Order {order['id']} references unknown restaurant {order['restaurant_id']}"
            )
        cart_id = order.get("cart_id")
        if cart_id is not None and cart_id not in cart_ids:
            problems.append(f"Order {order['id']} references unknown cart {cart_id}")
        for line in order["items"]:
            problems.extend(
                _check_item(
                    f"Order {order['id']}",
                    line["menu_item_id"],
                    order["restaurant_id"],
                    item_restaurant,
                )
            )

    return problems


def _check_item(
    owner: str,
    menu_item_id: str,
    restaurant_id: str | None,
    item_restaurant: dict[str, str],
) -> list[str]:
    if menu_item_id not in item_restaurant:
        return [f"{owner} references unknown menu item {menu_item_id}"]
    if restaurant_id is not None and item_restaurant[menu_item_id] != restaurant_id:
        return [f"{owner} has item {menu_item_id} from a different restaurant"]
    return []