from fastapi import APIRouter, HTTPException, Query, WebSocket, WebSocketDisconnect
from pymongo.errors import PyMongoError

from app.schemas.event_schema import DetectionEventCreate, DetectionEventUpdate
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


@router.patch("/{event_id}")
async def update_detection_event(event_id: str, update: DetectionEventUpdate):
    try:
        event = await event_service.update_event(event_id, update)
    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="이벤트 저장소에 연결할 수 없습니다.",
        ) from exc
    if event is None:
        raise HTTPException(status_code=404, detail="이벤트를 찾을 수 없습니다.")
    return {"success": True, "event": event}


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
