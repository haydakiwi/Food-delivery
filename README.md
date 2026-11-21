# Food Delivery API

Team: **Commit Crew**

The project uses the required **Route -> Service -> Repository -> JSON**
architecture. Milestone 1 provides restaurant discovery and menu browsing.
Milestone 2 integrates these into one working system: customer accounts,
authentication and authorization, a shopping cart with backend-calculated
totals, checkout, and persisted orders, all reachable through the REST API and
the browser frontend.

## M2 integrated workflow

```text
Customer -> Restaurant -> Menu -> Cart -> Checkout -> Order
```

1. Register (`POST /customers/register`) and sign in (`POST /auth/login`).
2. Browse, search, and filter restaurants, then open a menu.
3. Add menu items to the cart; the backend returns the subtotal, delivery fee,
   and total.
4. Check out (`POST /checkout`). Prices are re-read from the current menu, the
   order is saved, and only then is the cart closed.
5. Retrieve the new order (`GET /orders/{order_id}`) and the order history
   (`GET /orders`). Orders keep the price paid even if the menu changes later.

`tests/test_end_to_end_workflow.py` runs this whole flow through the API,
restarts the application, and checks the order is still there.

## Requirements

- Python 3.11 or newer
- `pip`

## Setup

```bash
git clone https://github.com/haydakiwi/Food-delivery.git
cd Food-delivery
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

On macOS/Linux, use `python3 -m venv .venv` and
`source .venv/bin/activate`.

## Run the application

From the repository root:

```bash
python -m uvicorn app.main:app --reload
```

Open the frontend at:

```text
http://127.0.0.1:8000/frontend/
```

FastAPI's generated API documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## Customer API

| Method | Path                                                | Purpose                                 |
| ------ | --------------------------------------------------- | --------------------------------------- |
| GET    | `/health`                                           | Confirm that the application is running |
| GET    | `/restaurants`                                      | List restaurants                        |
| GET    | `/restaurants/{restaurant_id}`                      | Get restaurant details                  |
| GET    | `/restaurants/{restaurant_id}/menu`                 | Get a restaurant menu                   |
| GET    | `/restaurants/{restaurant_id}/menu/items/{item_id}` | Get one menu item                       |
| GET    | `/docs`                                             | Generated Swagger/OpenAPI documentation |

## Customer accounts and authentication

| Method | Path                             | Purpose                                  |
| ------ | -------------------------------- | ---------------------------------------- |
| POST   | `/customers/register`            | Register a customer                      |
| POST   | `/auth/login`                    | Sign in and receive a bearer token       |
| GET    | `/customers/me`                  | Get the signed-in customer's profile     |
| PATCH  | `/customers/me`                  | Update profile and delivery addresses    |
| POST   | `/customers/me/deactivate`       | Deactivate the signed-in account         |
| GET    | `/customers/{customer_id}`       | Get a customer (administrator role only) |

Passwords are salted and hashed with PBKDF2-SHA256 before crossing the
repository boundary. API responses use the public customer schema and never
return a password hash. Protected operations require
`Authorization: Bearer <access_token>`; invalid or missing authentication
returns HTTP 401, while inactive accounts and insufficient roles return HTTP
403.

The seed customers use the password `Password123!`. `cust_003` is intentionally
inactive for demonstrating the deactivated-account rule.

## Cart, checkout, and orders

All cart, checkout, and order endpoints require an authenticated customer
bearer token using `Authorization: Bearer <access_token>`.

| Method | Path | Purpose |
| ------ | ---- | ------- |
| GET | `/carts` | Retrieve the signed-in customer's active cart |
| POST | `/carts` | Create an empty active cart |
| POST | `/carts/items` | Add a menu item to the active cart |
| PATCH | `/carts/items/{menu_item_id}` | Update the quantity of a cart item |
| DELETE | `/carts/items/{menu_item_id}` | Remove an item from the cart |
| DELETE | `/carts/items` | Clear the active cart |
| POST | `/checkout` | Create an order from the active cart |
| GET | `/orders` | Retrieve the signed-in customer's order history |
| GET | `/orders/{order_id}` | Retrieve one of the signed-in customer's orders |

Cart operations enforce business rules, including allowing items from only
one restaurant per cart, checking menu-item availability, rejecting
deactivated customers, allowing one active cart per customer, and limiting
item quantities to 1–50.

Every cart response includes `subtotal`, `delivery_fee`, and `total`,
calculated by the backend from current menu prices, so clients never
calculate prices themselves.

Checkout validates the cart and calculates item prices and delivery fees using
current server-side data. A delivery address may optionally be supplied in the
checkout request.

Orders are associated with the customer who placed them. Customers can only
retrieve their own orders: history is returned newest first, and requesting
another customer's order returns 404 so order IDs are not revealed. Each order
stores the item names and unit prices at checkout time.

In M2, newly created orders have the status `placed`. The full order-status
lifecycle is deferred to M3.

The restaurant list supports:

- `search` — case-insensitive restaurant-name search
- `cuisine` — case-insensitive cuisine filter
- `is_open` — filter by open/closed status

## Frontend

The frontend favours functionality over visual design. It provides:

- customer registration and sign-in (the bearer token is kept in the browser);
- restaurant listing, search, and cuisine/open-status filtering;
- restaurant details, menus, and menu items;
- adding menu items to the cart and viewing the cart;
- checkout and the customer's order history;
- a create/update restaurant form that calls the management API.

No data is hard-coded into the frontend. The browser calls the FastAPI
application with `fetch()` and displays the returned API data, including API
error messages. Business rules and prices are enforced by the backend only.

## Management API

The management form and the restaurant-management endpoints are:

```text
POST  /restaurants
PATCH /restaurants/{restaurant_id}
POST  /restaurants/{restaurant_id}/menu/items
PATCH /restaurants/{restaurant_id}/menu/items/{item_id}
```

These management endpoints do not currently require authentication.

The request body contains the restaurant fields:

```json
{
  "name": "Example Restaurant",
  "cuisine": "Japanese",
  "rating": 4.5,
  "delivery_time_minutes": 30,
  "delivery_fee": 2.99,
  "is_open": true,
  "address": "123 Main St"
}
```

## Data and configuration

Committed data lives in:

- `data/restaurants.json`
- `data/menu_items.json`
- `data/customers.json`
- `data/carts.json`
- `data/orders.json`

The application paths can be overridden with:

- `DATA_PATH`
- `MENU_ITEMS_PATH`
- `CUSTOMERS_PATH`
- `CARTS_PATH`
- `ORDERS_PATH`
- `AUTH_SECRET` — set this to a private random value outside local development
- `AUTH_TOKEN_TTL_SECONDS` — bearer-token lifetime (default: 3600 seconds)
- `PASSWORD_HASH_ITERATIONS` — PBKDF2 work factor (default: 100000)

Each data file has exactly one owning repository, built on the shared
`JsonRepository` base. IDs such as `cust_001`, `cart_001`, and `ord_001` are
stored in the files and never reused, so relationships survive restarts.
Writes go to a temporary file first and then replace the original, so a crash
cannot leave a half-written file.

Tests use temporary files and do not modify committed application data.

## Run the tests

```bash
python -m pytest -v
```

## Continuous Integration

GitHub Actions is configured in `.github/workflows/ci.yml`.

The workflow runs automatically on:

- pushes to `main`;
- pull requests targeting `main`; and
- manual workflow dispatch.

It installs the dependencies and executes the complete pytest suite on Python
3.11 and 3.12.

## Repository structure

```text
Food-delivery/
|-- .github/workflows/ci.yml
|-- app/
|   |-- api/routes/                 # HTTP route handlers
|   |-- core/config.py              # Application configuration
|   |-- repositories/               # JSON data access
|   |-- schemas/                    # Pydantic models
|   |-- services/                   # Business logic
|   `-- main.py                     # FastAPI application entry point
|-- data/                           # Persistent JSON data
|-- frontend/
|   |-- index.html                  # Browser UI
|   |-- app.js                      # API integration
|   `-- styles.css                  # Basic presentation
|-- docs/                           # Decision Receipt and provenance
|-- scrum/                          # Scrum meeting notes
|-- tests/                          # Automated tests
|-- requirements.txt
`-- README.md
```

## Request flow

A customer request follows:

```text
Frontend
   -> FastAPI Route
   -> Service
   -> Repository
   -> JSON data
```

For example, clicking **Checkout** in the frontend calls `POST /checkout`:

```text
routes/checkout.py::checkout            (authenticates the customer)
   -> services/checkout_service.py::checkout
        -> CustomerRepository, CartRepository, RestaurantRepository,
           MenuItemRepository                  (validate, re-read prices)
        -> OrderRepository.create             (writes data/orders.json)
        -> CartRepository.close               (writes data/carts.json)
```

The route handles HTTP concerns, the service contains business logic, the
repository reads/writes persistent data, and Pydantic models define the API
contract.

## M2 submission checklist

Before creating the immutable `m2-integrated-system` tag:

1. Run `python -m pytest -v` and confirm CI is green on `main`.
2. Start the application and walk through the full workflow in the frontend:
   register, sign in, browse a menu, add to cart, check out, view orders.
3. Demonstrate the business rules: a deactivated customer (`cust_003`), an
   unavailable item, an invalid quantity, items from two restaurants, and a
   price change before checkout.
4. Restart the application and confirm orders and carts persist.
5. Ensure every feature is linked to a GitHub issue and merged through a
   reviewed pull request, and the Project Board is up to date.
6. Update `docs/PROVENANCE.md`, `docs/DECISION_RECEIPT.md`, and the scrum notes.
7. Create the `m2-integrated-system` tag only after the final submission commit.
8. Record the full commit SHA in the Canvas submission.

Do not commit secrets, credentials, environment files, or access tokens.