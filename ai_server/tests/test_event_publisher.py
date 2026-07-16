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
