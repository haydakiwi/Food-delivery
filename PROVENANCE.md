# Provenance

The whole group has used AI for coding and generating ideas.


## Entry — Role C

- **Student(s):** Jay Patel
- **Artifact:** `app/schemas/restaurant.py`, `app/services/restaurant_service.py`, `app/api/routes/restaurants.py`, `app/main.py`, and `tests/test_restaurant_service.py`
- **Label:** AI-ASSISTED
- **AI tool:** ChatGPT
- **Purpose:** Used ChatGPT to help understand the Role C requirements, plan the implementation, troubleshoot integration issues, review the code, and assist with testing and Git/GitHub workflow.
- **Influence:** AI guidance helped with the structure and implementation of the Restaurant schema, service layer, `/restaurants` route, router integration, and service test. I reviewed and understood the code and made the final implementation decisions.
- **Validation:** Ran the pytest suite, manually tested the `/restaurants` and `/health` endpoints, verified the API through FastAPI Swagger documentation, and confirmed that the restaurant response matched the required Pydantic schema. The final integrated project passed all 14 tests.
- **PR or commit:** Role C implementation commit `292cd00`.


## Entry — Role A
 
- **Student(s):** Hayden
- **Artifact:** `app/main.py`, `app/core/config.py`, `.gitignore`, `requirements.txt`, project repository structure, and GitHub repository setup
- **Label:** AI-ASSISTED
- **AI tool:** Microsoft Copilot
- **Purpose:** Used Microsoft Copilot to help understand the M0 requirements, set up the FastAPI project structure, create the `/health` and initial `/restaurants` endpoints, configure Git/GitHub, create the `.gitignore` file, and clarify the required architecture and workflow.
- **Influence:** AI guidance helped with project setup, FastAPI configuration, endpoint implementation, repository organization, and Git commands. I reviewed, tested, and made the final implementation decisions myself.
- **Validation:** Successfully ran the FastAPI application using Uvicorn, verified the `/health` and `/restaurants` endpoints returned HTTP 200 responses, confirmed `/docs` was accessible, checked the project structure against the milestone requirements, and successfully committed and pushed changes to GitHub.
- **PR or commit:** Initial project foundation commits and subsequent setup/configuration commits.


## Entry — Milestone 1 Part B: Customer Endpoints

- **Student(s):** Shukan
- **Artifact:** `app/schemas/menu.py`, `app/services/restaurant_service.py`, `app/api/routes/restaurants.py`, `tests/conftest.py`, `tests/test_restaurant_service.py`, and `tests/test_restaurants.py`
- **Label:** AI-ASSISTED
- **AI tool:** OpenAI Codex
- **Purpose:** Used Codex to review the Milestone 1 requirements, plan the customer-facing API contract, implement the service and route layers, document the endpoints in OpenAPI, and create automated tests.
- **Influence:** AI assistance contributed to the restaurant search/filter logic, restaurant and menu lookup flows, domain not-found errors, HTTP 404 mapping, API descriptions and parameters, and isolated service and endpoint tests. I reviewed the implementation and remain responsible for understanding, validating, and explaining it.
- **Validation:** Ran the complete pytest suite and confirmed all 55 tests passed. Verified tests cover restaurant listing, case-insensitive search, combined filters, restaurant details, menu and item retrieval, unknown resources, cross-restaurant item protection, and generated OpenAPI documentation.
- **PR or commit:** Milestone 1 Part B customer-endpoints feature branch; update this field with the pull request or final commit before submission.
