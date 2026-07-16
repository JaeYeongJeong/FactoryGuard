from fastapi import APIRouter

from app.routers.vision_llm.kws_router import router as kws_router
from app.routers.vision_llm.rag_router import router as rag_router
from app.routers.vision_llm.reports_router import router as reports_router


router = APIRouter()
router.include_router(reports_router)
router.include_router(rag_router)
router.include_router(kws_router)
