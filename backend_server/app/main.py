from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.collections import create_indexes
from app.routers.ai_gateway_router import router as ai_gateway_router
from app.routers.events_router import router as events_router
from app.routers.reports_router import router as reports_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_indexes()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(events_router)
app.include_router(reports_router)
app.include_router(ai_gateway_router)

@app.get("/health")
def health_check():
    return {"status": "backend server ok"}
