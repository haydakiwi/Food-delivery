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
