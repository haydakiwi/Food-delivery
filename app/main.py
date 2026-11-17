from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes.customers import router as customers_router
from app.api.routes.restaurants import router as restaurants_router
from app.api.routes.carts import router as carts_router
from app.api.routes.checkout import router as checkout_router
from app.api.routes.orders import router as orders_router


app = FastAPI(
    title="Food Delivery API",
    description="Food delivery API with customer accounts and restaurant browsing.",
)

app.include_router(customers_router)
app.include_router(restaurants_router)
app.include_router(carts_router)
app.include_router(checkout_router)
app.include_router(orders_router)

app.mount("/frontend", StaticFiles(directory="frontend", html=True), name="frontend")


@app.get("/health", summary="Health check")
def health() -> dict[str, str]:
    return {"status": "ok"}
