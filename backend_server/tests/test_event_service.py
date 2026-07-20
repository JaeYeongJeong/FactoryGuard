import asyncio
import os
from datetime import datetime, timezone

import pytest
from pymongo.errors import DuplicateKeyError

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")

from app.schemas.event_schema import DetectionEventCreate, DetectionEventUpdate
from app.services.event_service import EventService


class FakeCollection:
    def __init__(self) -> None:
        self.documents = []

    def insert_one(self, document: dict) -> None:
        if any(item["event_id"] == document["event_id"] for item in self.documents):
            raise DuplicateKeyError("duplicate event")
        self.documents.append(dict(document))

    def find_one_and_update(self, query: dict, update: dict, **_kwargs):
        for document in self.documents:
            if document["event_id"] == query["event_id"]:
                document.update(update["$set"])
                return dict(document)
        return None


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


def test_event_response_is_updated_and_streamed() -> None:
    collection = FakeCollection()
    collection.documents.append({
        "event_id": "event-003",
        "timestamp": datetime(2026, 7, 16, tzinfo=timezone.utc),
        "status": "entered",
    })
    manager = FakeConnectionManager()
    service = EventService(collection=collection, connection_manager=manager)

    updated = asyncio.run(service.update_event(
        "event-003",
        DetectionEventUpdate(
            response_status="resolved",
            response_memo="현장 조치 완료",
        ),
    ))

    assert updated["status"] == "entered"
    assert updated["response_status"] == "resolved"
    assert updated["response_memo"] == "현장 조치 완료"
    assert manager.events == [updated]


def test_lifecycle_update_does_not_create_duplicate_event() -> None:
    collection = FakeCollection()
    manager = FakeConnectionManager()
    service = EventService(collection=collection, connection_manager=manager)
    started_at = datetime(2026, 7, 16, tzinfo=timezone.utc)

    entered = DetectionEventCreate(
        event_id="incident-001",
        camera_id="cam-01",
        timestamp=started_at,
        last_seen_at=started_at,
        event_type="intrusion",
        severity="high",
        status="entered",
        worker_id=7,
        zone_name="위험구역",
        message="침입 감지",
    )
    exited = entered.model_copy(update={
        "status": "exited",
        "last_seen_at": datetime(2026, 7, 16, 0, 0, 15, tzinfo=timezone.utc),
        "exited_at": datetime(2026, 7, 16, 0, 0, 15, tzinfo=timezone.utc),
        "duration": 15.0,
        "message": "침입 상태 해제",
    })

    asyncio.run(service.create_event(entered))
    updated = asyncio.run(service.create_event(exited))

    assert len(collection.documents) == 1
    assert updated["timestamp"] == "2026-07-16T00:00:00+00:00"
    assert updated["status"] == "exited"
    assert updated["duration"] == 15.0
    assert updated["exited_at"] == "2026-07-16T00:00:15+00:00"
    assert manager.events[-1] == updated
