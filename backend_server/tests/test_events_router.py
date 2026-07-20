import os

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")

from fastapi.testclient import TestClient

import app.main as backend_main
from app.routers import events_router
from app.services.event_connection_manager import event_connection_manager
from app.services.event_service import EventService


class FakeCollection:
    def __init__(self) -> None:
        self.documents = []

    def insert_one(self, document: dict) -> None:
        self.documents.append(dict(document))


def test_saved_event_is_streamed_to_frontend(monkeypatch) -> None:
    collection = FakeCollection()
    service = EventService(
        collection=collection,
        connection_manager=event_connection_manager,
    )
    monkeypatch.setattr(events_router, "event_service", service)
    monkeypatch.setattr(backend_main, "create_indexes", lambda: None)
    payload = {
        "event_id": "event-stream-001",
        "camera_id": "cam-01",
        "timestamp": "2026-07-16T04:30:00+00:00",
        "event_type": "intrusion",
        "severity": "critical",
        "status": "entered",
        "worker_id": 12,
        "zone_name": "프레스 위험구역",
        "message": "작업자 12의 위험구역 침입이 감지되었습니다.",
        "snapshot_url": "http://localhost:8001/captures/event.jpg",
    }

    with TestClient(backend_main.app) as client:
        with client.websocket_connect("/events/stream") as websocket:
            response = client.post("/events/detect", json=payload)
            streamed = websocket.receive_json()

    assert response.status_code == 200
    assert collection.documents[0]["event_id"] == payload["event_id"]
    assert streamed == {
        **payload,
        "last_seen_at": None,
        "exited_at": None,
        "duration": 0.0,
        "response_status": None,
    }
