"""위험 이벤트 저장과 프론트엔드 실시간 전송을 담당합니다."""

import asyncio

from pymongo import DESCENDING
from pymongo.errors import DuplicateKeyError

from app.db.collections import event_collection
from app.schemas.event_schema import DetectionEventCreate
from app.services.event_connection_manager import (
    EventConnectionManager,
    event_connection_manager,
)


class EventService:
    def __init__(
        self,
        collection=event_collection,
        connection_manager: EventConnectionManager = event_connection_manager,
    ) -> None:
        self._collection = collection
        self._connection_manager = connection_manager

    @staticmethod
    def _serialize(document: dict) -> dict:
        document = dict(document)
        document.pop("_id", None)
        timestamp = document.get("timestamp")
        if hasattr(timestamp, "isoformat"):
            document["timestamp"] = timestamp.isoformat()
        return document

    async def create_event(self, event_data: DetectionEventCreate) -> dict:
        document = event_data.model_dump()
        created = True
        try:
            await asyncio.to_thread(self._collection.insert_one, document)
        except DuplicateKeyError:
            created = False
            existing = await asyncio.to_thread(
                self._collection.find_one,
                {"event_id": event_data.event_id},
            )
            if existing is None:
                raise
            document = existing

        serialized = self._serialize(document)
        if created:
            await self._connection_manager.broadcast(serialized)
        return serialized

    async def get_recent_events(self, limit: int = 50) -> list[dict]:
        def fetch_events():
            cursor = (
                self._collection.find({})
                .sort("timestamp", DESCENDING)
                .limit(limit)
            )
            return list(cursor)

        documents = await asyncio.to_thread(fetch_events)
        return [self._serialize(document) for document in documents]


event_service = EventService()
