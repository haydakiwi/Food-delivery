# Food Delivery API

Team: **Food Delivery**

This repository contains the M0 foundation for a small FastAPI food-delivery
backend. It exposes a health check and a restaurant-list endpoint using the
required Route -> Service -> Repository -> JSON architecture.

## Requirements

- Python 3.11 or newer
- `pip`

## Setup

Clone the repository and enter the project directory:

```bash
git clone https://github.com/haydakiwi/Food-delivery.git
cd Food-delivery
```

Create and activate a virtual environment on macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate it with:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run the application

From the repository root, run:

```bash
python -m uvicorn app.main:app --reload
```

The development server is available at `http://127.0.0.1:8000`.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| GET | `/health` | Confirm that the application is running |
| GET | `/restaurants` | Return the restaurant list |
| GET | `/docs` | Open the generated Swagger/OpenAPI documentation |

Example requests:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/restaurants
```

## Data and configuration

Committed restaurant data lives in `data/restaurants.json`. The application
data path is configurable with the `DATA_PATH` environment variable so tests
can use temporary data without changing the committed file.

Example:

```bash
DATA_PATH=/path/to/restaurants.json python -m uvicorn app.main:app
```

Each restaurant uses these fields:

- `id`
- `name`
- `cuisine`
- `rating`
- `delivery_time_minutes`
- `delivery_fee`
- `is_open`
- `address`

## Run the tests

Run the complete test suite from the repository root:

```bash
python -m pytest
```

For more detail:

```bash
python -m pytest -v
```

The tests create their own restaurant files in pytest temporary directories.
They never modify `data/restaurants.json`. The suite covers the health endpoint,
the restaurant-list endpoint, the response fields, a missing data file, and an
invalid JSON file.

## Repository structure

```text
Food-delivery/
|-- app/
|   |-- api/routes/                 # HTTP route handlers
|   |-- core/config.py              # Application configuration
|   |-- repositories/               # JSON data access
|   |-- schemas/                    # Pydantic response models
|   |-- services/                   # Business logic
|   `-- main.py                     # FastAPI application entry point
|-- data/restaurants.json           # Committed restaurant data
|-- scrum/team-agreement.md         # Versioned team agreement
|-- tests/                           # Fixtures and automated tests
|-- requirements.txt                # Python dependencies
`-- README.md
```

## Request flow

`GET /restaurants` follows this path:

```text
Route -> Service -> Repository -> data/restaurants.json
```

Routes handle HTTP concerns, services contain business logic, repositories read
the data source, and Pydantic schemas define the API response.

## Clean-setup check

Before creating the submission tag, a team member who did not write this README
should perform these steps from a fresh clone:

1. Create and activate a new virtual environment.
2. Install `requirements.txt`.
3. Run `python -m pytest`.
4. Start the server with `python -m uvicorn app.main:app`.
5. Visit `/health`, `/restaurants`, and `/docs`.

Do not commit secrets, credentials, environment files, or access tokens.
