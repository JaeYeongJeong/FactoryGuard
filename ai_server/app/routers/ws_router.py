from fastapi import APIRouter, WebSocket

from app.services.websocket_service import websocket_service


router = APIRouter(
    prefix="/ws",
    tags=["ws"],
)


@router.get("/health")
def health():
    return websocket_service.get_health()


@router.websocket("/cameras/{camera_id}")
async def camera_ingest(
    websocket: WebSocket,
    camera_id: str,
):
    """
    Camera Agent 연결 엔드포인트입니다.

    첫 메시지:
        카메라 등록 JSON

    이후 메시지:
        JPEG 바이너리 프레임
    """
    await websocket_service.handle_camera(
        websocket=websocket,
        camera_id=camera_id,
    )


@router.websocket("/view/{camera_id}")
async def camera_view(
    websocket: WebSocket,
    camera_id: str,
):
    """React 또는 브라우저가 처리된 영상을 수신하는 엔드포인트입니다."""
    await websocket_service.handle_viewer(
        websocket=websocket,
        camera_id=camera_id,
    )