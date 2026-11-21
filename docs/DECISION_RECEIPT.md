# M1 Decision Receipt

## Decision

Serve the M1 browser frontend from the same FastAPI application instead of
requiring a separate frontend development server.

## Context

The M1 frontend must communicate with the REST API, but the milestone does not
grade visual polish. The team needed a simple way to demonstrate a working
customer flow and avoid unnecessary frontend infrastructure.

## Options considered

1. Serve static frontend files from FastAPI.
2. Create a separate frontend application with its own development server.
3. Leave the frontend as a static file opened directly in the browser.

## Decision

We chose option 1: FastAPI serves the frontend files under `/frontend/`.

## Rationale

- Keeps the M1 demonstration simple.
- Lets the frontend call the API using same-origin requests.
- Avoids adding an unnecessary frontend build system.
- Keeps the frontend clearly separated from backend business logic.
- Makes a fresh-clone demonstration easier because one server starts the
  complete M1 application.

## Trade-offs

The frontend is intentionally lightweight and does not provide the tooling or
component structure of a larger production frontend. That is acceptable for
M1 because the assignment explicitly prioritizes functionality over visual
design.

## Consequences

The FastAPI application mounts the `frontend/` directory. The browser UI can
retrieve restaurants and menus from the same application and can submit
management requests to the API without additional cross-origin configuration.

## Validation

The decision is considered successful when a fresh project setup can:

1. Start FastAPI.
2. Open `/frontend/`.
3. Retrieve the restaurant list from the API.
4. Open restaurant details and menus.
5. Submit a management form successfully once the management endpoints are
   available.

---

# M2 Decision Receipt

## Evidence baseline

This receipt records the implemented M2 design at commit `ab191c8`. At the
time this receipt was prepared, the complete automated suite passed with 236
tests. File names, methods, tests, commits, and pull requests below refer to
artifacts that exist in the repository. Known limitations are stated
explicitly rather than presented as completed behaviour.

## 1. Integration boundaries and ownership

### Problem

The Customer, Restaurant, Menu, Cart, Checkout, and Order subsystems need to
work together without placing business rules in the browser or duplicating
them across API routes.

### Decision

Use the existing `Route -> Service -> Repository -> JSON` boundary throughout
M2:

- routes own HTTP input, authentication dependencies, status codes, and error
  translation;
- services own business rules and cross-subsystem coordination;
- repositories own record loading, validation, stable IDs, and persistence;
- JSON files own the persisted records; and
- Pydantic schemas define request, response, and stored-data contracts.

`CheckoutService.checkout` is the coordinator for the main M2 workflow. It
uses the Customer, Cart, Restaurant, MenuItem, and Order repositories rather
than making one repository responsible for unrelated records.

### Alternative considered

The `/checkout` route could call each repository directly and perform the
workflow itself.

### Benefit and cost

The chosen boundary makes the same rules reusable by HTTP endpoints and
direct service tests, and it keeps persistence details out of routes. The cost
is more interfaces and dependency wiring in `app/api/routes/checkout.py` and
`app/services/checkout_service.py`.

### Request trace

For `POST /checkout`:

1. `app/api/routes/checkout.py::checkout` resolves `CurrentCustomer` and
   translates service exceptions into HTTP responses.
2. `app/services/checkout_service.py::CheckoutService.checkout` validates the
   customer and active cart.
3. It reads the current restaurant and each current menu item through their
   repositories.
4. It constructs and validates `OrderCreate` using server-calculated prices.
5. `OrderRepository.create` writes the order to `data/orders.json`.
6. Only after that succeeds, `CartRepository.close` updates
   `data/carts.json`.
7. The route returns the created `Order` with HTTP 201.

### Evidence

- `app/api/routes/checkout.py::checkout`
- `app/services/checkout_service.py::CheckoutService.checkout`
- `tests/test_checkout.py::test_customer_can_checkout_and_cart_is_closed`
- `tests/test_checkout_service.py::test_checkout_creates_order_and_closes_cart`
- PR #30

## 2. Cross-subsystem business-rule ownership

### Cart rule: one restaurant per active cart

**Problem:** A cart containing items from several restaurants would have an
ambiguous restaurant, delivery fee, and checkout owner.

**Decision:** `CartService.add_item` reads the menu item through
`MenuItemRepository` and compares its `restaurant_id` with the cart's stored
`restaurant_id`. It raises `DifferentRestaurantError` before updating the
cart. The route maps this rule failure to HTTP 409.

**Alternative:** Allow mixed-restaurant carts and split them into several
orders during checkout.

**Benefit and cost:** Checkout has one restaurant and one delivery fee. The
cost is that a customer must use a separate cart/order for another restaurant.

**Evidence:**

- `app/services/cart_service.py::CartService.add_item`
- `tests/test_cart_service.py::test_add_item_from_different_restaurant_is_rejected`
- `tests/test_carts.py::test_customer_cannot_add_item_from_different_restaurant`

### Checkout rule: revalidate current availability and prices

**Problem:** A menu item's price or availability may change after it is added
to the cart. A browser-sent or cart-cached value may therefore be stale or
tampered with.

**Decision:** `CheckoutService.checkout` re-reads every menu item and the
restaurant immediately before order creation. It rejects missing,
unavailable, or cross-restaurant items and calculates all monetary values on
the backend.

**Alternative:** Store and trust the price captured when the item is added to
the cart or accept a total from the frontend.

**Benefit and cost:** Checkout uses authoritative current data and does not
trust the client. The cost is additional repository reads during checkout.

**Evidence:**

- `app/services/checkout_service.py::CheckoutService.checkout`
- `tests/test_checkout_service.py::test_checkout_uses_current_menu_price_and_name`
- `tests/test_checkout.py::test_checkout_uses_current_menu_price`
- `tests/test_checkout.py::test_checkout_rejects_item_that_became_unavailable`

The unavailable-item API test also confirms that a rejected checkout leaves
the cart active.

### Why these rules live in services

Keeping the rules in services protects callers other than the current browser
and avoids duplicating logic across routes. The rejected alternative was to
enforce the rules only with frontend controls or route-level conditionals.
Frontend validation remains useful for feedback, but the backend is the
authoritative enforcement boundary.

## 3. Checkout, prices, and initial order creation

### Checkout sequence

**Problem:** Clearing a cart before an order is safely saved could lose a
customer's selected items.

**Decision:** The implemented order is:

1. validate the active customer;
2. retrieve and validate the active, non-empty cart;
3. retrieve the current restaurant;
4. re-read and validate every menu item;
5. calculate line totals, subtotal, delivery fee, and total;
6. validate and save the order; and
7. close the cart only after the order save succeeds.

**Alternative:** Close the cart before saving the order.

**Benefit and cost:** A failed order save leaves the cart available for retry.
The remaining cost is that order save and cart close are two separate file
writes rather than one transaction.

**Evidence:**

- `app/services/checkout_service.py::CheckoutService.checkout`
- `tests/test_checkout_service.py::test_failed_order_save_leaves_cart_active`
- `tests/test_checkout_service.py::test_checkout_rejects_second_checkout_of_closed_cart`

### Source of truth for prices and totals

`MenuItemRepository` and `data/menu_items.json` are authoritative for current
item names, prices, and availability. `RestaurantRepository` and
`data/restaurants.json` are authoritative for the current delivery fee. The
backend calculates:

- `line_total = unit_price * quantity`;
- `subtotal = sum(line_total)`; and
- `total = subtotal + delivery_fee`.

`OrderCreate` independently validates those relationships before
`OrderRepository.create` writes anything. An order stores a snapshot of the
item name, unit price, line total, restaurant name, delivery fee, and total so
later menu changes do not rewrite the original transaction.

**Alternative:** Reconstruct old orders from current menu records whenever
they are retrieved.

**Benefit and cost:** The saved order preserves what was purchased and at
what price. The cost is duplicated descriptive and price data in order
records.

**Evidence:**

- `app/schemas/order.py::OrderCreate`
- `app/repositories/order_repository.py::OrderRepository.create`
- `tests/test_order_repository.py::test_create_rejects_inconsistent_totals_and_changes_nothing`
- `tests/test_persistence_integration.py::test_customer_cart_order_workflow_survives_restart`

### Save-failure behaviour and remaining consistency limitation

If `OrderRepository.create` fails, the exception propagates and the cart is
not closed. This is verified by
`test_failed_order_save_leaves_cart_active`.

If the order is saved but closing the cart fails, the implementation raises
`CheckoutCartCloseError`, which the route reports as HTTP 500. In that case,
the saved order may coexist with an active cart. There is no rollback or
cross-file transaction, so the receipt does not claim atomicity across
`orders.json` and `carts.json`.

## 4. Persistence and data consistency

### Record ownership

| Record | Owning repository | Persisted file | Relationship approach |
| --- | --- | --- | --- |
| Customer | `CustomerRepository` | `data/customers.json` | Stable `customer_id`; deactivation instead of deletion |
| Restaurant | `RestaurantRepository` | `data/restaurants.json` | Stable `restaurant_id` |
| Menu item | `MenuItemRepository` | `data/menu_items.json` | References `restaurant_id` |
| Cart | `CartRepository` | `data/carts.json` | References customer, restaurant, and menu-item IDs |
| Order | `OrderRepository` | `data/orders.json` | References IDs and stores the transaction snapshot |

### Decision

Active carts store menu-item references and quantities rather than copied
prices. Orders store immutable transaction snapshots. Repositories share
`JsonRepository` for loading, stable ID allocation, protected IDs, duplicate
ID checks, and atomic replacement of one JSON file.

### Alternatives considered

- Store price snapshots in the cart.
- Reconstruct historical orders entirely from current menu records.
- Keep duplicated load/save/ID logic in every repository.

### Benefit and cost

Reference-based carts avoid stale checkout prices, while snapshot-based orders
preserve transaction history. The shared repository base removes duplicated
persistence behaviour. The costs are cross-file references that require
integrity checks and coupling to the common repository abstraction.

### File-write behaviour and limitations

`JsonRepository._save` writes a `.tmp` file and calls `os.replace`, so each
individual JSON-file replacement is atomic. The system does not implement
locking for concurrent load-modify-save operations, and a multi-file checkout
is not atomic as a unit.

### Evidence

- `app/repositories/json_repository.py`
- `app/repositories/integrity.py::find_relationship_problems`
- `tests/test_persistence_integration.py::test_committed_seed_data_relationships_are_valid`
- `tests/test_persistence_integration.py::test_customer_cart_order_workflow_survives_restart`
- PRs #24, #25, #26, and #27

## 5. Individual architecture and design improvements

### Janhvi - shared JSON persistence boundary

**Before:** Restaurant and MenuItem repositories contained repeated JSON
loading, saving, stable-ID, and validation behaviour.

**After:** `JsonRepository` owns the common persistence algorithm, and the
Customer, Cart, Order, Restaurant, and MenuItem repositories specialize their
record rules.

**Alternative:** Keep independent persistence implementations.

**Benefit:** Consistent validation, stable IDs, and atomic per-file saves.

**Cost:** Changes to the base class can affect every repository.

**Evidence:** PR #24, commits `f8f48f3` and `efb954c`, and the repository and
persistence-integration tests.

### Shukan - centralized authentication boundary and safe partial updates

**Before:** M1 had no shared authenticated-customer or role dependency. During
review, the optional update schema also allowed explicit nulls for required
stored fields, which could modify JSON before response validation failed.

**After:** `AuthService`, `CurrentCustomer`, and `require_roles` centralize
token resolution, active-customer checks, and role authorization. The update
schema distinguishes an omitted field from an explicitly null required field,
rejecting invalid requests before persistence.

**Alternative:** Repeat token and role checks in each route and allow the
service or repository to discover invalid nulls later.

**Benefit:** Consistent HTTP 401/403 behaviour, reusable authorization, no
password hash in public responses, and no stored-data modification for the
reviewed null-update defect.

**Cost:** Protected endpoints depend on the shared auth configuration and
custom signed-token implementation.

**Evidence:** PR #29; commits `4d3dfa6` and `9af0a5b`;
`tests/test_customers.py::test_explicit_null_update_returns_422_without_changing_data`;
and `tests/test_customers.py::test_admin_lookup_enforces_role_and_returns_public_customer`.

### Jay - service-owned cart and checkout coordination

**Before:** The repositories existed, but the application had no service
boundary coordinating cart rules, current menu data, order creation, and cart
closure.

**After:** `CartService` owns cart invariants and `CheckoutService` owns the
multi-repository checkout sequence. Routes translate typed domain errors into
documented HTTP responses.

**Alternative:** Put orchestration directly in the FastAPI route or inside one
large repository.

**Benefit:** Business rules can be tested without HTTP and persistence owners
remain separate.

**Cost:** The services require several repository dependencies and explicit
error mapping.

**Evidence:** PR #30, commit `08574ff`, `tests/test_cart_service.py`, and
`tests/test_checkout_service.py`.

### Hayden - review-driven frontend trust-boundary hardening

**Before:** The M1 frontend did not support the authenticated customer flow.
The first M2 version also used hard-coded registration address data, did not
handle a missing active cart, and inserted some API-provided strings without
escaping.

**After:** The frontend accepts real registration data, handles an empty cart,
disables unavailable-item controls, and escapes API-provided strings before
inserting them into generated markup. It integrates login, menu browsing,
cart addition, checkout, and order history with the same-origin API.

**Alternative:** Display raw API values and rely entirely on backend rejection
or introduce a separate frontend framework and build server.

**Benefit:** Safer rendering and more resilient browser behaviour without a
second deployment/build system.

**Cost:** The vanilla-JavaScript UI still requires manual DOM and state
management.

**Evidence:** PR #33 and review-response commits `eae1452` and `dab1ffd`.

Jay's review of PR #33 provides additional peer-review evidence. The review
identified hard-coded registration data, unsafe rendering of API-provided
order values, missing handling for a `null` active-cart response, an accidental
test restaurant in seed data, missing required-field validation, and an
unescaped cart item ID. The resulting changes collected registration values
from the form, escaped dynamic values, handled an empty cart, disabled
unavailable items, restored the committed seed data, added registration
validation, and escaped the cart item ID. Evidence is recorded in the PR #33
conversation and review-response commits `eae1452`, `99b5d18`, `b8d20f3`, and
`dab1ffd`.

## 6. Verification summary

The M2 implementation is supported by repository, service, API, authorization,
failure-path, persistence-restart, integration, and OpenAPI tests. The suite at
the evidence baseline passed 236 tests.

Representative evidence includes:

- `tests/test_customers.py::test_integrated_registration_login_profile_and_menu_flow`
- `tests/test_persistence_integration.py::test_customer_cart_order_workflow_survives_restart`
- `tests/test_checkout.py::test_customer_can_checkout_and_cart_is_closed`
- `tests/test_checkout_service.py::test_failed_order_save_leaves_cart_active`
- `tests/test_customers.py::test_explicit_null_update_returns_422_without_changing_data`

## 7. Known gaps at this baseline

These items are not claimed as complete by this receipt:

- the cart API returns stored item references and quantities but not an
  authoritative cart subtotal/total;
- the frontend does not yet provide quantity-update or remove-item controls,
  although the backend supports both operations;
- the frontend also lacks a clear-cart control, although the backend supports
  clearing the active cart;
- the order API returns customer order history but has no
  `GET /orders/{order_id}` endpoint;
- checkout has no cross-file rollback if the order saves and cart closure then
  fails; and
- JSON persistence has no concurrent-writer locking.

The first three are M2 requirement gaps to resolve before the assessed tag.
The final two are documented consistency limitations rather than behaviours
the implementation claims to provide.
