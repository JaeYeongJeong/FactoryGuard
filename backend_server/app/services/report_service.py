import asyncio

from pymongo import DESCENDING
from pymongo.errors import DuplicateKeyError

from app.db.collections import incident_report_collection
from app.schemas.report_schema import IncidentReportCreate


class ReportService:
    def __init__(self, collection=incident_report_collection) -> None:
        self._collection = collection

    @staticmethod
    def _serialize(document: dict | None) -> dict | None:
        if document is None:
            return None
        result = dict(document)
        result.pop("_id", None)
        created_at = result.get("created_at")
        if hasattr(created_at, "isoformat"):
            result["created_at"] = created_at.isoformat()
        return result

    async def create_report(self, report: IncidentReportCreate) -> dict:
        document = report.model_dump()
        # 기존 배포본의 incident_id 고유 인덱스와 호환합니다.
        document["incident_id"] = report.report_id
        try:
            await asyncio.to_thread(self._collection.insert_one, document)
        except DuplicateKeyError:
            document = await asyncio.to_thread(
                self._collection.find_one,
                {"report_id": report.report_id},
            )
            if document is None:
                raise
        return self._serialize(document)

    async def get_report(self, report_id: str) -> dict | None:
        document = await asyncio.to_thread(
            self._collection.find_one,
            {"report_id": report_id},
        )
        return self._serialize(document)

    async def list_reports(self, limit: int = 50) -> list[dict]:
        def fetch():
            return list(
                self._collection.find({})
                .sort("created_at", DESCENDING)
                .limit(limit)
            )

        return [self._serialize(item) for item in await asyncio.to_thread(fetch)]


report_service = ReportService()
