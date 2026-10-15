from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.restaurants import router as restaurants_router

app = FastAPI(
    title="Food Delivery API",
    description="Restaurant discovery and menu browsing API.",
)

app.include_router(restaurants_router)
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")


@app.get("/health", summary="Health check")
def health() -> dict[str, str]:
    return {"status": "ok"}
