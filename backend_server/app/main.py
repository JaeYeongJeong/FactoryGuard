from fastapi import FastAPI

from app.db.collections import create_indexes
from app.routers.events_router import router as events_router
from app.routers.reports_router import router as reports_router

app = FastAPI()

app.include_router(events_router)
app.include_router(reports_router)

@app.on_event("startup")
def startup():
    create_indexes()

@app.get("/health")
def health_check():
    return {"status": "backend server ok"}
