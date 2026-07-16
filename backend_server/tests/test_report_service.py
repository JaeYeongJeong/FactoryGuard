import asyncio
import os
from datetime import datetime, timezone

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")

from app.schemas.report_schema import IncidentReportCreate
from app.services.report_service import ReportService


class FakeCursor:
    def __init__(self, documents: list[dict]) -> None:
        self.documents = documents

    def sort(self, *_args):
        return self

    def limit(self, limit: int):
        self.documents = self.documents[:limit]
        return self

    def __iter__(self):
        return iter(self.documents)


class FakeCollection:
    def __init__(self) -> None:
        self.documents = []

    def insert_one(self, document: dict) -> None:
        self.documents.append(dict(document))

    def find_one(self, query: dict):
        return next(
            (
                item
                for item in self.documents
                if all(item.get(key) == value for key, value in query.items())
            ),
            None,
        )

    def find(self, _query: dict):
        return FakeCursor(list(self.documents))


def test_report_is_saved_and_can_be_loaded() -> None:
    collection = FakeCollection()
    service = ReportService(collection=collection)
    report = IncidentReportCreate(
        report_id="report-001",
        event_id="event-001",
        source="vision_llm_rag",
        created_at=datetime(2026, 7, 16, tzinfo=timezone.utc),
        report="사고 분석 결과",
        recommended_action=["설비를 정지한다."],
        rag_available=True,
    )

    saved = asyncio.run(service.create_report(report))
    loaded = asyncio.run(service.get_report("report-001"))

    assert collection.documents[0]["incident_id"] == "report-001"
    assert saved["report_id"] == "report-001"
    assert loaded["event_id"] == "event-001"
    assert loaded["created_at"] == "2026-07-16T00:00:00+00:00"
