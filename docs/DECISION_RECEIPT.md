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
