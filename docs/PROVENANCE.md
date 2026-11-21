# Provenance


## Entry — Role A
- **Student(s):** Janhvi
- **Artifact:** `app/core/config.py`, `app/schemas/menu_item.py`, `app/repositories/restaurant_repository.py`, `app/repositories/menu_item_repository.py`, `data/menu_items.json`, `tests/test_restaurant_repository.py`, and `tests/test_menu_item_repository.py`
- **Label:** AI-ASSISTED
- **AI tool:** ChatGPT
- **Purpose:** Used AI to assist with understanding the Milestone 1 Role A requirements, planning the data-layer and persistence implementation, reviewing repository logic, troubleshooting issues, and assisting with testing and Git/GitHub workflow.
- **Influence:** AI guidance assisted with the MenuItem request/data models, Restaurant and MenuItem repository operations, stable ID generation, JSON persistence, validation of stored data, atomic file saving, and repository test coverage. I reviewed and understood the implementation, tested the repository behavior, and made the final implementation decisions.
- **Validation:** Ran the automated pytest suite and verified repository behavior for reading, creating, and updating restaurants and menu items. Verified stable ID generation, persistence across repository restarts, invalid/missing JSON handling, duplicate-ID detection, protection of IDs during updates, restaurant-linked menu items, and atomic file saving. The completed Milestone 1 project passed all 77 automated tests on the final merged `main`.
- **PR or commit:** Role A implementation PR #11 and associated Role A commits.


## Entry — Role B

- **Student(s):** Shukan
- **Artifact:** `app/schemas/menu.py`, `app/services/restaurant_service.py`, `app/api/routes/restaurants.py`, `tests/conftest.py`, `tests/test_restaurant_service.py`, and `tests/test_restaurants.py`
- **Label:** AI-ASSISTED
- **AI tool:** ChatGPT
- **Purpose:** Used AI to assist with understanding the Milestone 1 Role B requirements, planning the customer-facing restaurant and menu endpoints, reviewing service and route logic, troubleshooting implementation issues, and assisting with testing and Git/GitHub workflow.
- **Influence:** AI guidance assisted with restaurant search and filtering, restaurant detail retrieval, menu and menu-item retrieval, service-layer error handling, HTTP 404 responses, OpenAPI documentation, isolated test fixtures, and automated service and endpoint test coverage. I reviewed and understood the implementation, tested the customer-facing API behavior, and made the final implementation decisions.
- **Validation:** Ran the automated pytest suite and verified restaurant listing, case-insensitive name search, cuisine and open-status filtering, restaurant detail retrieval, restaurant menus, individual menu-item retrieval, unknown restaurant and menu-item handling, prevention of cross-restaurant menu-item access, and OpenAPI documentation. The completed Milestone 1 project passed all 77 automated tests on the final merged `main`.
- **PR or commit:** Role B implementation PR #12 and associated Role B commits.

## Entry — Role C

- **Student(s):** Jay Patel
- **Artifact:** `app/schemas/restaurant.py`, `app/services/restaurant_service.py`, `app/api/routes/restaurants.py`, `tests/test_restaurant_service.py`, and `tests/test_restaurants.py`
- **Label:** AI-ASSISTED
- **AI tool:** ChatGPT
- **Purpose:** Used ChatGPT to help interpret the Milestone 1 Role C requirements, plan the management endpoint implementation, review existing repository and customer-endpoint code, troubleshoot integration and test issues, review code changes, and assist with Git/GitHub workflow.
- **Influence:** AI guidance assisted with the Restaurant create/update request models, restaurant and menu-item management service methods, POST/PATCH routes, validation and error handling, business rules such as duplicate restaurant-name rejection and restaurant/menu-item ownership checks, and service/endpoint test coverage. I reviewed and understood the implementation, ran the code and tests, resolved issues found during integration, and made the final implementation decisions.
- **Validation:** Ran the complete pytest suite and verified all 77 tests passed. Verified successful and failure cases for restaurant and menu-item creation/update, HTTP 400/404/422 responses, JSON persistence, and OpenAPI documentation. 
- **PR or commit:** Role C implementation commit `c8dc948` and merged PR #15; integration test restoration commit `a8f67de`.


## Entry — Role D

- **Student(s):** Hayden
- **Artifact:** `frontend/index.html`, `frontend/app.js`, `frontend/styles.css`, `.github/workflows/ci.yml`, `app/main.py`, `README.md`, `docs/DECISION_RECEIPT.md`, and project submission/documentation files
- **Label:** AI-ASSISTED
- **AI tool:** ChatGPT
- **Purpose:** Used AI to assist with understanding the Milestone 1 Role D requirements, planning and implementing the frontend, integrating the frontend with the FastAPI backend, configuring continuous integration, preparing project documentation, troubleshooting integration issues, and assisting with Git/GitHub workflow.
- **Influence:** AI guidance assisted with the restaurant frontend interface, API requests between the frontend and backend, restaurant and menu display, restaurant create/update functionality, frontend styling, serving the frontend through FastAPI, GitHub Actions CI configuration, README documentation, and the Milestone 1 Decision Receipt. I reviewed and understood the implementation, tested the integrated application, and made the final implementation decisions.
- **Validation:** Ran the automated pytest suite and verified all 77 tests passed. Verified the `/health`, restaurant filtering, menu retrieval, `/frontend/`, and `/docs` endpoints, checked the frontend JavaScript, and tested frontend-to-backend integration. An integration issue where the frontend used `PUT` while the backend update endpoint required `PATCH` was corrected and revalidated. The final merged `main` passed the complete automated test suite and GitHub CI checks.
- **PR or commit:** Role D Milestone 1 implementation commits and subsequent frontend `PATCH` integration-fix PR.


Milestone #2

## Entry — M2 Member 1 (Data Models, Repositories and Persistence)

- **Student(s):** Janhvi
- **Artifact:** `app/repositories/json_repository.py`, `app/repositories/restaurant_repository.py`, `app/repositories/menu_item_repository.py`, `app/schemas/customer.py`, `app/schemas/cart.py`, `app/schemas/order.py`, `app/repositories/customer_repository.py`, `app/repositories/cart_repository.py`, `app/repositories/order_repository.py`, `app/repositories/integrity.py`, `app/core/config.py`, `data/customers.json`, `data/carts.json`, `data/orders.json`, `tests/test_customer_repository.py`, `tests/test_cart_repository.py`, `tests/test_order_repository.py`, and `tests/test_persistence_integration.py`
- **Label:** AI-ASSISTED
- **AI tool:** Claude
- **Purpose:** Used AI to plan the Milestone 2 data-layer work, split it into GitHub Issues, guide the shared repository refactor, help learn about the Customer, Cart and Order models, repositories, seed data and tests, and diagnose test and CI failures.
- **Influence:** For the JsonRepository refactor (Issue 1), I worked through it with AI guidance: AI explained what to move into the base class, and I updated the restaurant and menu item repositories; AI identified fixes for missing `return` statements and a missing `typing` import that only failed CI on Python 3.11/3.12. For Issues 2–4, AI taught how to write the Customer, Cart and Order models and repositories, the cross-file integrity check, the seed data and the repository and integration tests. I wrote the code in the project, ran the tests, reviewed the design decisions (cart stores item references not prices, orders store a price snapshot, orders are append-only, one active cart per customer, deactivated customers are kept rather than deleted), and coordinated the repository interfaces with Shukan and Jay.
- **Validation:** Ran the full pytest suite locally and through GitHub Actions CI. The original 77 M1 tests pass unchanged after the refactor, and the full suite passes with 147 tests on the final branch. Verified stable IDs, persistence across repository restarts, rejection of duplicate emails, invalid quantities, second active carts and inconsistent order totals without modifying the data file, validity of committed seed data, and cross-file relationship integrity in an integrated Customer → Menu → Cart → Order test with a simulated restart.
- **PR or commit:** PR #24 (JsonRepository refactor), PR #25 (Customer), PR #26 (Cart), PR #27 (Order).

## Entry — M2 Member 2 (Customer Accounts and Authentication)

### Student

- **Name:** Shukan
- **GitHub:** Shukan1712

### Contributions

- Implemented customer registration and sign-in API workflows.
- Implemented PBKDF2-SHA256 password hashing and password verification.
- Ensured repositories receive `password_hash` values and never plain-text passwords.
- Implemented signed, expiring bearer authentication tokens.
- Added shared `CurrentCustomer` and `require_roles` FastAPI dependencies.
- Implemented authenticated customer profile retrieval and updates.
- Implemented delivery-address updates and account deactivation.
- Added active-customer and administrator-role authorization checks.
- Returned `CustomerPublic` from API operations so password hashes are not exposed.
- Added duplicate-email handling with HTTP 409 responses.
- Fixed explicit-null profile updates after peer review so invalid values return HTTP 422 before persistence.
- Added OpenAPI, service, API, authentication, authorization, and integration tests.

### Pull Request

- PR #29: Customer accounts and authentication.

### Issue

- Issue #28, linked from PR #29 using `Closes #28`.

### Commits

- `4d3dfa6`: Implement customer accounts and authentication.
- `9af0a5b`: Reject null customer updates.

### Files Modified

- `app/api/dependencies/__init__.py`
- `app/api/dependencies/auth.py`
- `app/api/routes/customers.py`
- `app/core/config.py`
- `app/main.py`
- `app/schemas/auth.py`
- `app/schemas/customer.py`
- `app/services/auth_service.py`
- `app/services/customer_service.py`
- `tests/conftest.py`
- `tests/test_auth_service.py`
- `tests/test_customer_service.py`
- `tests/test_customers.py`
- `README.md`
- `PROVENANCE.md`

### Testing Performed

- Verified registration hashes passwords and never returns password hashes.
- Verified valid login returns a bearer token and public customer data.
- Verified incorrect passwords, malformed tokens, expired tokens, and deactivated customers are rejected.
- Verified customer profile retrieval, updates, address changes, and deactivation.
- Verified customer and administrator role restrictions.
- Verified duplicate-email registration and updates do not modify stored JSON.
- Verified explicit `null` values for required profile fields return HTTP 422 without modifying stored JSON.
- Added a multi-subsystem registration -> login -> profile -> restaurant-menu test.
- Verified customer/authentication OpenAPI schemas do not expose `password_hash`.
- Ran the complete suite successfully with 236 tests at the M2 evidence baseline.

### AI Assistance

- **Label:** AI-ASSISTED
- **Tool:** ChatGPT/Codex
- **Purpose:** Used AI to help interpret M2 requirements, plan the customer/authentication architecture, review code, diagnose issues, strengthen validation and tests, and assist with Git/GitHub workflow.
- **Influence:** AI guidance assisted with the service and dependency boundaries, password/token security review, error handling, regression testing, and the explicit-null peer-review fix. I reviewed and understood the implementation and made the final implementation decisions.

### Evidence

- PR #29 was reviewed and merged into `main`.
- The peer-review finding about explicit-null updates was addressed in commit `9af0a5b`.
- Representative regression test: `tests/test_customers.py::test_explicit_null_update_returns_422_without_changing_data`.
- Representative integration test: `tests/test_customers.py::test_integrated_registration_login_profile_and_menu_flow`.

## Entry — M2 Member 3 (Cart, Checkout, and Order APIs)

- **Student(s):** Jay
- **Artifact:** `app/api/routes/carts.py`, `app/api/routes/checkout.py`, `app/api/routes/orders.py`, `app/services/cart_service.py`, `app/services/checkout_service.py`, `app/main.py`, `tests/conftest.py`, `tests/test_carts.py`, `tests/test_cart_service.py`, `tests/test_checkout.py`, and `tests/test_checkout_service.py`
- **Label:** AI-ASSISTED
- **AI tool:** ChatGPT
- **Purpose:** Used ChatGPT to help interpret the Cart, Checkout, and Order API requirements, plan the implementation, review the route and service-layer design, testing issues and assist with Git/GitHub workflow.
- **Influence:** AI guidance assisted with implementing authenticated cart operations, cart validation and business rules, checkout validation and order creation, customer-specific order retrieval, API error handling, and automated test coverage. I reviewed/understood then made final implementation decisions, and performed the integration and testing.
- **Validation:** Ran the complete automated pytest suite and verified that all 236 tests passed. Tests covered cart operations, authentication and authorization, cart business rules, checkout validation, order creation, persistence, and customer-specific order retrieval.
- **PR or commit:** PR #30 — Implement Cart, Checkout, and Order APIs.

## Entry — M2 Member 4 (Customer Frontend Workflow)

### Student

- **Name:** Hayden Lin
- **GitHub:** haydakiwi

### Contributions

- Implemented complete customer-facing frontend workflow.
- Added customer registration form and backend integration.
- Added customer login form and authentication integration.
- Implemented restaurant browsing and restaurant detail views.
- Implemented menu display and Add To Cart functionality.
- Added shopping cart integration with backend APIs.
- Added checkout workflow integration.
- Added order history display and rendering.
- Added frontend error handling and user feedback.
- Added registration field validation.
- Added safe HTML escaping for API-provided values.
- Added empty-cart handling and unavailable-item handling.

### Pull Requests

- PR #32: Add customer registration and login frontend integration.
- PR #33: Complete customer frontend workflow.

### Issue

- Issue #34: Customer Frontend Workflow Integration.

### Files Modified

- `frontend/index.html`
- `frontend/app.js`

### Testing Performed

- Registered customer accounts through the frontend UI.
- Logged in using the frontend authentication flow.
- Browsed restaurants and menus.
- Added items to cart.
- Loaded and viewed cart contents.
- Completed checkout flow.
- Viewed order history.
- Verified validation and error-handling behavior.

### Evidence

- Reviewed PR #33 with feedback addressed.
- CI checks passing on Python 3.11 and Python 3.12.
- Linked work item: Issue #34.
- Review-response commits `eae1452` and `dab1ffd`.
