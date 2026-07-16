from fastapi import APIRouter

from app.routers.vision_llm.reports_router import router as reports_router


router = APIRouter()
router.include_router(reports_router)
