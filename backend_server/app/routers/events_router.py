from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from pymongo.errors import PyMongoError

from app.schemas.event_schema import DetectionEventCreate
from app.services.event_connection_manager import event_connection_manager
from app.services.event_service import event_service


router = APIRouter(prefix="/events", tags=["events"])


@router.post("/detect")
async def receive_detection_event(event_data: DetectionEventCreate):
    try:
        saved_event = await event_service.create_event(event_data)
        return {"success": True, "event": saved_event}
    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="이벤트 저장소에 연결할 수 없습니다.",
        ) from exc


@router.get("")
async def get_recent_events(limit: int = Query(default=50, ge=1, le=200)):
    try:
        return {"events": await event_service.get_recent_events(limit)}
    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="이벤트 저장소에 연결할 수 없습니다.",
        ) from exc


@router.websocket("/stream")
async def stream_events(websocket: WebSocket):
    await event_connection_manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        event_connection_manager.disconnect(websocket)
    except Exception:
        event_connection_manager.disconnect(websocket)
