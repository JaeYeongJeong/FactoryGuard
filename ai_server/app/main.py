from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers.vision_ai import router as vision_ai_router
from app.routers.vision_llm import router as vision_llm_router
from app.services.vision_ai.capture_service import CaptureService
from app.services.vision_ai.runtime_service import vision_ai_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    vision_ai_service.start()
    try:
        yield
    finally:
        vision_ai_service.stop()


app = FastAPI(
    title="FactoryGuard AI Server",
    description="실시간 위험구역 침입 및 이상 자세 감지 분석 엔진 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(vision_ai_router)
app.include_router(vision_llm_router)
app.mount(
    "/captures",
    StaticFiles(
        directory=str(
            CaptureService(settings.event.snapshot_dir, enabled=False).capture_dir
        ),
        check_dir=False,
    ),
    name="captures",
)
