import os

DATA_PATH = os.getenv("DATA_PATH", "data/restaurants.json")
MENU_ITEMS_PATH = os.getenv("MENU_ITEMS_PATH", "data/menu_items.json")
CUSTOMERS_PATH = os.getenv("CUSTOMERS_PATH", "data/customers.json")
CARTS_PATH = os.getenv("CARTS_PATH", "data/carts.json")
ORDERS_PATH = os.getenv("ORDERS_PATH", "data/orders.json")

# Authentication defaults are suitable for local development and tests. A deployed
# environment must override AUTH_SECRET with a private, randomly generated value.
AUTH_SECRET = os.getenv("AUTH_SECRET", "development-only-change-me")
AUTH_TOKEN_TTL_SECONDS = int(os.getenv("AUTH_TOKEN_TTL_SECONDS", "3600"))
PASSWORD_HASH_ITERATIONS = int(os.getenv("PASSWORD_HASH_ITERATIONS", "100000"))
