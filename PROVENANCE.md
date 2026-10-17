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
