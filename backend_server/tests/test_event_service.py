import asyncio
import os
from datetime import datetime, timezone

import pytest

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")

from app.schemas.event_schema import DetectionEventCreate
from app.services.event_service import EventService


class FakeCollection:
    def __init__(self) -> None:
        self.documents = []

    def insert_one(self, document: dict) -> None:
        self.documents.append(dict(document))


class FakeConnectionManager:
    def __init__(self) -> None:
        self.events = []

    async def broadcast(self, event: dict) -> None:
        self.events.append(event)


class FailingCollection:
    def insert_one(self, document: dict) -> None:
        raise RuntimeError("database unavailable")


def test_event_is_broadcast_after_database_insert() -> None:
    collection = FakeCollection()
    manager = FakeConnectionManager()
    service = EventService(collection=collection, connection_manager=manager)
    event = DetectionEventCreate(
        event_id="event-001",
        camera_id="cam-01",
        timestamp=datetime(2026, 7, 16, tzinfo=timezone.utc),
        event_type="intrusion",
        severity="critical",
        status="entered",
        worker_id=3,
        zone_name="프레스 위험구역",
        message="위험구역 침입이 감지되었습니다.",
        snapshot_url="http://localhost:8001/captures/event.jpg",
    )

    saved = asyncio.run(service.create_event(event))

    assert collection.documents[0]["event_id"] == "event-001"
    assert manager.events == [saved]
    assert saved["timestamp"] == "2026-07-16T00:00:00+00:00"


def test_database_failure_is_not_broadcast() -> None:
    manager = FakeConnectionManager()
    service = EventService(
        collection=FailingCollection(),
        connection_manager=manager,
    )
    event = DetectionEventCreate(
        event_id="event-002",
        camera_id="cam-01",
        timestamp=datetime(2026, 7, 16, tzinfo=timezone.utc),
        event_type="fall_down",
        severity="critical",
        status="entered",
        worker_id=4,
        zone_name="전체 영역",
        message="쓰러짐이 감지되었습니다.",
    )

    with pytest.raises(RuntimeError, match="database unavailable"):
        asyncio.run(service.create_event(event))

    assert manager.events == []
