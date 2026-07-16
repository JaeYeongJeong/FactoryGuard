from fastapi import APIRouter

from app.routers.vision_ai.health_router import router as health_router
from app.routers.vision_ai.ws_router import router as ws_router
from app.routers.vision_ai.zones_router import router as zones_router


router = APIRouter()
router.include_router(health_router)
router.include_router(zones_router)
router.include_router(ws_router)
