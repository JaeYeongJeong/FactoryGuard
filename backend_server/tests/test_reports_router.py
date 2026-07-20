import asyncio
import os

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")

from fastapi.testclient import TestClient

import app.main as backend_main
from app.routers import reports_router


class FakeReportService:
    def __init__(self) -> None:
        self.reports = {}

    async def create_report(self, report):
        payload = report.model_dump(mode="json")
        self.reports[report.report_id] = payload
        return payload

    async def get_report(self, report_id: str):
        return self.reports.get(report_id)

    async def list_reports(self, limit: int):
        return list(self.reports.values())[:limit]


class FakeAIGatewayService:
    def __init__(self) -> None:
        self.request = None

    async def analyze_image(self, **kwargs):
        self.request = kwargs
        return {"success": True, "report_id": "report-ai-001"}


class FakeEventService:
    async def get_event(self, event_id: str):
        return {
            "event_id": event_id,
            "snapshot_url": "https://ai.example.com/captures/event.jpg",
        }


class FakeSnapshotService:
    async def fetch(self, snapshot_url: str):
        assert snapshot_url == "https://ai.example.com/captures/event.jpg"
        return "event.jpg", b"captured-jpeg", "image/jpeg"


def test_report_can_be_saved_and_loaded(monkeypatch) -> None:
    service = FakeReportService()
    monkeypatch.setattr(reports_router, "report_service", service)
    monkeypatch.setattr(backend_main, "create_indexes", lambda: None)
    payload = {
        "report_id": "report-router-001",
        "event_id": "event-001",
        "source": "vision_llm_rag",
        "created_at": "2026-07-16T04:30:00+00:00",
        "report": "Vision LLM 사고 분석 결과",
        "legal_basis": [],
        "recommended_action": ["설비를 정지한다."],
        "rag_available": True,
        "metadata": {},
    }

    with TestClient(backend_main.app) as client:
        created = client.post("/reports", json=payload)
        loaded = client.get("/reports/report-router-001")

    assert created.status_code == 200
    assert created.json()["report"]["report_id"] == "report-router-001"
    assert loaded.status_code == 200
    assert loaded.json()["report"]["event_id"] == "event-001"


def test_event_capture_is_forwarded_to_report_analysis(monkeypatch) -> None:
    gateway = FakeAIGatewayService()
    monkeypatch.setattr(reports_router, "ai_gateway_service", gateway)
    monkeypatch.setattr(reports_router, "event_service", FakeEventService())
    monkeypatch.setattr(reports_router, "snapshot_service", FakeSnapshotService())

    result = asyncio.run(reports_router.analyze_event_report("event-001"))

    assert result["report_id"] == "report-ai-001"
    assert gateway.request == {
        "path": "/reports/analyze-with-legal-basis",
        "filename": "event.jpg",
        "content": b"captured-jpeg",
        "content_type": "image/jpeg",
        "event_id": "event-001",
    }
