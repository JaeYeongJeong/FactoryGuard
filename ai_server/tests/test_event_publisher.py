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
        zone_id="press-zone",
        zone_name="프레스 위험구역",
        duration=0.0,
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
        "last_seen_at",
        "exited_at",
        "duration",
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
        zone_id="demo-zone-1",
        zone_name="demo-zone-1",
        duration=0.0,
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


def test_lifecycle_events_reuse_incident_id() -> None:
    publisher = EventPublisher(
        backend_url="http://backend:8000",
        ai_public_url="https://ai.example.com",
    )

    def event(status: str, timestamp: float, duration: float):
        return SimpleNamespace(
            event_type=status,
            timestamp=timestamp,
            threat_type="intrusion",
            zone_severity="high",
            tracker_id=7,
            zone_id="zone-1",
            zone_name="위험구역",
            duration=duration,
        )

    entered = publisher.build_payload(event("entered", 100.0, 0.0), "cam-01")
    staying = publisher.build_payload(event("staying", 110.0, 10.0), "cam-01")
    exited = publisher.build_payload(event("exited", 115.0, 15.0), "cam-01")
    next_entered = publisher.build_payload(
        event("entered", 120.0, 0.0),
        "cam-01",
    )

    assert entered["event_id"] == staying["event_id"] == exited["event_id"]
    assert entered["timestamp"] == staying["timestamp"] == exited["timestamp"]
    assert staying["duration"] == 10.0
    assert exited["exited_at"] == "1970-01-01T00:01:55+00:00"
    assert next_entered["event_id"] != entered["event_id"]
