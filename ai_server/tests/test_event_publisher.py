from pathlib import Path
from types import SimpleNamespace

from app.services.vision_ai.communication.event_publisher import EventPublisher


def test_event_payload_matches_frontend_contract() -> None:
    publisher = EventPublisher(
        backend_url="http://backend:8000",
        ai_public_url="https://ai.example.com",
    )
    event = SimpleNamespace(
        event_type="entered",
        timestamp=1_700_000_000.0,
        threat_type="intrusion",
        zone_severity="critical",
        tracker_id=12,
        zone_name="프레스 위험구역",
    )

    payload = publisher.build_payload(
        event,
        camera_id="cam-01",
        snapshot_path=Path("/tmp/danger frame.jpg"),
    )

    assert set(payload) == {
        "event_id",
        "camera_id",
        "timestamp",
        "event_type",
        "severity",
        "status",
        "worker_id",
        "zone_name",
        "message",
        "snapshot_url",
    }
    assert payload["camera_id"] == "cam-01"
    assert payload["event_type"] == "intrusion"
    assert payload["severity"] == "critical"
    assert payload["status"] == "entered"
    assert payload["worker_id"] == 12
    assert payload["snapshot_url"] == "https://ai.example.com/captures/danger%20frame.jpg"


def test_capture_base_url_is_used_without_modification() -> None:
    publisher = EventPublisher(
        backend_url="http://backend:8000",
        ai_public_url="http://localhost:8001",
        capture_base_url="https://ai.j-jandy.com/captures/",
    )
    event = SimpleNamespace(
        event_type="entered",
        timestamp=1_700_000_000.0,
        threat_type="intrusion",
        zone_severity="critical",
        tracker_id=23,
        zone_name="demo-zone-1",
    )

    payload = publisher.build_payload(
        event,
        camera_id="cam-01",
        snapshot_path=Path("/tmp/20260716_150903_639_cam-01_intrusion_worker-23_demo-zone-1.jpg"),
    )

    assert payload["snapshot_url"] == (
        "https://ai.j-jandy.com/captures/"
        "20260716_150903_639_cam-01_intrusion_worker-23_demo-zone-1.jpg"
    )
