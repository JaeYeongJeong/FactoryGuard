from fastapi import FastAPI

from app.db.collections import create_indexes
from app.routers import web

app = FastAPI()

app.include_router(web.router)

@app.on_event("startup")
def startup():
    create_indexes()

@app.get("/health")
def health_check():
    return {"status": "backend serverok"}
