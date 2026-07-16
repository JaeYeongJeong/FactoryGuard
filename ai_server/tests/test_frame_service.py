import numpy as np

from app.services.vision_ai.frame_service import FrameService


class FakeProcessor:
    def __init__(self) -> None:
        self.frames = []

    def process(self, frame: np.ndarray, show_display: bool = True):
        self.frames.append((frame, show_display))
        return frame + 1, ["danger-event"]


class FakeEncodedFrame:
    def tobytes(self) -> bytes:
        return b"encoded-jpeg"


class FakeCaptureService:
    def __init__(self) -> None:
        self.calls = []

    def save_danger_frame(self, frame, event, camera_id):
        self.calls.append((frame, event, camera_id))
        return None


class FakeEventPublisher:
    def __init__(self) -> None:
        self.calls = []

    def publish(self, event, camera_id, snapshot_path):
        self.calls.append((event, camera_id, snapshot_path))


def test_frame_service_bridges_jpeg_to_vision_pipeline(monkeypatch) -> None:
    decoded = np.zeros((2, 2, 3), dtype=np.uint8)
    resized = np.zeros((3, 4, 3), dtype=np.uint8)
    processor = FakeProcessor()
    capture_service = FakeCaptureService()
    event_publisher = FakeEventPublisher()
    service = FrameService(
        processor,
        resize=(4, 3),
        capture_service=capture_service,
        event_publisher=event_publisher,
    )

    monkeypatch.setattr(
        "app.services.vision_ai.frame_service.cv2.imdecode",
        lambda frame_array, mode: decoded,
        raising=False,
    )
    monkeypatch.setattr(
        "app.services.vision_ai.frame_service.cv2.resize",
        lambda frame, size: resized,
        raising=False,
    )
    monkeypatch.setattr(
        "app.services.vision_ai.frame_service.cv2.imencode",
        lambda extension, frame, params: (True, FakeEncodedFrame()),
        raising=False,
    )

    frame_bytes, events = service.process_frame(b"raw-jpeg", "cam-01")

    assert frame_bytes == b"encoded-jpeg"
    assert events == ["danger-event"]
    assert processor.frames[0][1] is True
    np.testing.assert_array_equal(processor.frames[0][0], resized)
    assert capture_service.calls[0][1:] == ("danger-event", "cam-01")
    assert event_publisher.calls == [("danger-event", "cam-01", None)]
