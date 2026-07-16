from fastapi import APIRouter, HTTPException

from app.services.event_service import event_service
from app.schemas.event_schema import DetectionEventCreate

router = APIRouter(
    prefix="/events",
    tags=["events"],
)


@router.post("/detect")
async def receive_detection_event(
    event_data:  DetectionEventCreate,
):
    try:
        saved_event = await event_service.create_event(
            event_data
        )

        return {
            "success": True,
            "event": saved_event,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="이벤트 저장 중 오류가 발생했습니다.",
        ) from exc