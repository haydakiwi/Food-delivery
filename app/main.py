from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.customers import router as customers_router
from app.api.routes.restaurants import router as restaurants_router

app = FastAPI(
    title="Food Delivery API",
    description="Food delivery API with customer accounts and restaurant browsing.",
)

app.include_router(customers_router)
app.include_router(restaurants_router)
app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")

@app.get("/health", summary="Health check")
def health() -> dict[str, str]:
    return {"status": "ok"}
