from fastapi import APIRouter

from app.services.vision_ai.runtime_service import vision_ai_service


router = APIRouter(tags=["health"])


@router.get("/health")
def health_check():
    return vision_ai_service.get_health()
