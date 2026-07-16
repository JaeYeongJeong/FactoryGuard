from types import SimpleNamespace

import numpy as np

from app.services.vision_ai.capture_service import CaptureService


def make_event(event_type: str):
    return SimpleNamespace(
        event_type=event_type,
        timestamp=1_700_000_000.123,
        threat_type="intrusion",
        tracker_id=7,
        zone_id="zone-A",
    )


def test_capture_service_saves_only_entered_events(tmp_path, monkeypatch) -> None:
    written_paths = []
    monkeypatch.setattr(
        "app.services.vision_ai.capture_service.cv2.imwrite",
        lambda path, frame: written_paths.append(path) or True,
        raising=False,
    )
    service = CaptureService(str(tmp_path))
    frame = np.zeros((2, 2, 3), dtype=np.uint8)

    saved = service.save_danger_frames(
        frame,
        [make_event("entered"), make_event("staying")],
        "cam-01",
    )

    assert len(saved) == 1
    assert len(written_paths) == 1
    assert "cam-01_intrusion_worker-7_zone-A.jpg" in written_paths[0]
