import numpy as np

from app.services.frame_service import FrameService


class FakeProcessor:
    def __init__(self) -> None:
        self.frames = []

    def process(self, frame: np.ndarray, show_display: bool = True):
        self.frames.append((frame, show_display))
        return frame + 1, ["danger-event"]


class FakeEncodedFrame:
    def tobytes(self) -> bytes:
        return b"encoded-jpeg"


def test_frame_service_bridges_jpeg_to_vision_pipeline(monkeypatch) -> None:
    decoded = np.zeros((2, 2, 3), dtype=np.uint8)
    resized = np.zeros((3, 4, 3), dtype=np.uint8)
    processor = FakeProcessor()
    service = FrameService(processor, resize=(4, 3))

    monkeypatch.setattr(
        "app.services.frame_service.cv2.imdecode",
        lambda frame_array, mode: decoded,
        raising=False,
    )
    monkeypatch.setattr(
        "app.services.frame_service.cv2.resize",
        lambda frame, size: resized,
        raising=False,
    )
    monkeypatch.setattr(
        "app.services.frame_service.cv2.imencode",
        lambda extension, frame, params: (True, FakeEncodedFrame()),
        raising=False,
    )

    frame_bytes, events = service.process_frame(b"raw-jpeg", "cam-01")

    assert frame_bytes == b"encoded-jpeg"
    assert events == ["danger-event"]
    assert processor.frames[0][1] is True
    np.testing.assert_array_equal(processor.frames[0][0], resized)
