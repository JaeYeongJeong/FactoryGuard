import asyncio
import json

from fastapi import WebSocketDisconnect

from app.services.websocket_service import WebSocketService


class FakeFrameService:
    def __init__(self) -> None:
        self.received = []

    def process_frame(self, frame_bytes: bytes, camera_id: str):
        self.received.append((frame_bytes, camera_id))
        return b"processed-jpeg", [object()]


class FakeCameraWebSocket:
    def __init__(self, registration: dict, frames: list[bytes]) -> None:
        self.registration = registration
        self.frames = iter(frames)
        self.accepted = False
        self.sent_json = []
        self.closed = None

    async def accept(self) -> None:
        self.accepted = True

    async def receive_text(self) -> str:
        return json.dumps(self.registration)

    async def receive_bytes(self) -> bytes:
        try:
            return next(self.frames)
        except StopIteration as exc:
            raise WebSocketDisconnect() from exc

    async def send_json(self, data: dict) -> None:
        self.sent_json.append(data)

    async def close(self, code: int, reason: str) -> None:
        self.closed = (code, reason)


class FakeViewer:
    def __init__(self) -> None:
        self.frames = []

    async def send_bytes(self, frame: bytes) -> None:
        self.frames.append(frame)


def test_camera_frame_is_processed_and_broadcast() -> None:
    frame_service = FakeFrameService()
    service = WebSocketService(frame_service=frame_service)
    camera = FakeCameraWebSocket({"type": "register"}, [b"raw-jpeg"])
    viewer = FakeViewer()
    service.viewers["cam-01"].add(viewer)

    asyncio.run(service.handle_camera(camera, "cam-01"))

    assert camera.accepted is True
    assert camera.sent_json[0]["type"] == "registered"
    assert frame_service.received == [(b"raw-jpeg", "cam-01")]
    assert service.latest_frames["cam-01"] == b"processed-jpeg"
    assert viewer.frames == [b"processed-jpeg"]


def test_camera_is_closed_when_pipeline_is_not_ready() -> None:
    service = WebSocketService()
    camera = FakeCameraWebSocket({"type": "register"}, [])

    asyncio.run(service.handle_camera(camera, "cam-01"))

    assert camera.closed == (1011, "vision pipeline is not ready")
