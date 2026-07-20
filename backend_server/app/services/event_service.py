"""위험 이벤트 저장과 프론트엔드 실시간 전송을 담당합니다."""

import asyncio

from pymongo import DESCENDING, ReturnDocument
from pymongo.errors import DuplicateKeyError

from app.db.collections import event_collection
from app.schemas.event_schema import DetectionEventCreate, DetectionEventUpdate
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
        for field in ("timestamp", "last_seen_at", "exited_at"):
            value = document.get(field)
            if hasattr(value, "isoformat"):
                document[field] = value.isoformat()
        return document

    async def create_event(self, event_data: DetectionEventCreate) -> dict:
        document = event_data.model_dump()
        try:
            await asyncio.to_thread(self._collection.insert_one, document)
        except DuplicateKeyError:
            lifecycle_update = {
                "status": event_data.status,
                "last_seen_at": event_data.last_seen_at,
                "exited_at": event_data.exited_at,
                "duration": event_data.duration,
                "message": event_data.message,
                "severity": event_data.severity,
            }
            lifecycle_update = {
                key: value
                for key, value in lifecycle_update.items()
                if value is not None
            }
            existing = await asyncio.to_thread(
                self._collection.find_one_and_update,
                {"event_id": event_data.event_id},
                {"$set": lifecycle_update},
                return_document=ReturnDocument.AFTER,
            )
            if existing is None:
                raise
            document = existing

        serialized = self._serialize(document)
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

    async def update_event(
        self,
        event_id: str,
        update: DetectionEventUpdate,
    ) -> dict | None:
        values = update.model_dump(exclude_none=True)
        document = await asyncio.to_thread(
            self._collection.find_one_and_update,
            {"event_id": event_id},
            {"$set": values},
            return_document=ReturnDocument.AFTER,
        )
        serialized = self._serialize(document)
        if serialized is not None:
            await self._connection_manager.broadcast(serialized)
        return serialized


event_service = EventService()
