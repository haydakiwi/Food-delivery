# Provenance

The whole group has used AI for coding and generating ideas.


## Role C — Schema, Service, and Route
**AI use classification:** AI-ASSISTED

AI was used to help understand the project requirements, plan the implementation steps, review code, troubleshoot integration issues, and verify Git/GitHub workflow.

The Role C implementation included:
- Creating the Pydantic `Restaurant` schema.
- Creating the `RestaurantService` layer.
- Creating the `GET /restaurants` FastAPI route.
- Connecting the restaurant router to the main FastAPI application.
- Adding a service-layer test using a fake repository.
- Integrating and testing the Role C implementation with the repository layer.

AI assistance was used for guidance, explanations, debugging, and code review. I reviewed and understood the implementation, tested the functionality, and validated the final work using pytest and the FastAPI Swagger documentation.

**Validation performed:**
- Ran the project test suite with pytest.
- Verified the `/restaurants` endpoint returned HTTP 200 and the expected restaurant data.
- Verified the endpoint response matched the Pydantic `Restaurant` schema.
- Tested integration between the route, service, and repository layers.