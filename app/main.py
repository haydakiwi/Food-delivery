from fastapi import FastAPI

from app.api.routes.restaurants import router as restaurants_router 

app = FastAPI()

app.include_router(restaurants_router) 

@app.get("/health")
def health():
    return {"status": "ok"}


