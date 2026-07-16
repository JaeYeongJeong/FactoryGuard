from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.services.vision_ai.runtime_service import vision_ai_service


router = APIRouter(prefix="/api", tags=["zones"])


@router.get("/zones")
def get_current_zones():
    return {"zones": vision_ai_service.get_zones()}


@router.post("/zones")
def add_custom_zone(zone_data: dict):
    added_zone = vision_ai_service.add_zone(zone_data)
    if added_zone is not None:
        return {"success": True, "added_zone_id": added_zone.zone_id}

    if not vision_ai_service.get_health()["websocket_pipeline_ready"]:
        return JSONResponse(
            status_code=503,
            content={"error": "서버 초기화 미완료"},
        )

    return JSONResponse(
        status_code=400,
        content={"error": "구역 파싱 실패. 최소 3개 이상 points 필요"},
    )
