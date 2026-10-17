# Food Delivery API

Team: **Food Delivery**

Milestone 1 implements an integrated restaurant-discovery and menu-browsing
vertical slice using the required **Route -> Service -> Repository -> JSON**
architecture. A small browser frontend consumes the REST API for customer
browsing and restaurant create/update operations.

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

The restaurant list supports:

- `search` — case-insensitive restaurant-name search
- `cuisine` — case-insensitive cuisine filter
- `is_open` — filter by open/closed status

## Frontend

The frontend is intentionally simple because M1 prioritizes functionality over
visual design. It provides:

- restaurant listing from the real API;
- search and cuisine/open-status filtering;
- restaurant details;
- restaurant menu and menu-item display;
- a create/update restaurant form that calls the management API.

Restaurant data is never hard-coded into the frontend. The browser calls the
FastAPI application with `fetch()` and displays the returned API data.

## Management API

The management form is designed to use the team's restaurant-management
endpoints:

```text
POST /restaurants
PATCH  /restaurants/{restaurant_id}
```

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

The management endpoints are implemented in the team's management feature.

## Data and configuration

Committed data lives in:

- `data/restaurants.json`
- `data/menu_items.json`

The application paths can be overridden with:

- `DATA_PATH`
- `MENU_ITEMS_PATH`

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
|-- docs/                           # M1 documentation
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

For example, selecting a restaurant in the frontend calls
`GET /restaurants/{restaurant_id}` and
`GET /restaurants/{restaurant_id}/menu`.

The route handles HTTP concerns, the service contains business logic, the
repository reads/writes persistent data, and Pydantic models define the API
contract.

## M1 submission checklist

Before creating the immutable `m1-vertical-slice` tag:

1. Run `python -m pytest -v`.
2. Start the application and test `/health`, `/restaurants`, `/docs`, and the
   frontend.
3. Verify the frontend can retrieve restaurants and menus from the API.
4. Verify the management form against the team's management endpoints.
5. Ensure every implementation feature is linked to a GitHub issue.
6. Ensure merged code was reviewed through a pull request.
7. Update `PROVENANCE.md` and the Decision Receipt.
8. Update all scrum notes.
9. Create the `m1-vertical-slice` tag only after the final submission commit.
10. Record the full commit SHA in the Canvas PDF.

Do not commit secrets, credentials, environment files, or access tokens.
