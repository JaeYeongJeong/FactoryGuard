from app.services.vision_llm.kws.schemas import SimulateKwsRequest
from app.services.vision_llm.kws.service import KwsService


class FakeBackendClient:
    def __init__(self) -> None:
        self.events = []
        self.reports = []

    def create_event(self, payload: dict) -> dict:
        self.events.append(payload)
        return {"success": True, "event": payload}

    def create_report(self, payload: dict) -> dict:
        self.reports.append(payload)
        return {"success": True, "report": payload}


class FakeRagResult:
    def model_dump(self) -> dict:
        return {
            "event_id": "kws-event",
            "route": "safety",
            "event_summary": "비상정지",
            "recommended_action": ["설비를 정지한다."],
            "legal_basis": [],
            "llm_context": {},
            "markdown": "# 비상정지 보고서",
        }


class FakeRagEngine:
    def build_report_basis(self, **kwargs):
        return FakeRagResult()


class FailingRagEngine:
    def build_report_basis(self, **kwargs):
        raise RuntimeError("RAG index unavailable")


def test_kws_detection_is_saved_as_backend_danger_event() -> None:
    backend = FakeBackendClient()
    service = KwsService(backend_client=backend)

    result = service.simulate(
        SimulateKwsRequest(
            text="멈춰 위험해",
            location="컨베이어 1번 라인",
            line_id="line-1",
        )
    )

    assert result.detection.detected is True
    assert result.backend_saved is True
    assert result.stop_command.accepted is True
    assert backend.events[0]["event_type"] == "kws_emergency_stop"
    assert backend.events[0]["camera_id"] == "line-1"
    assert backend.events[0]["zone_name"] == "컨베이어 1번 라인"


def test_kws_rag_report_is_saved_to_backend() -> None:
    backend = FakeBackendClient()
    service = KwsService(
        backend_client=backend,
        rag_engine=FakeRagEngine(),
    )

    result = service.simulate(
        SimulateKwsRequest(text="stop", call_rag=True)
    )

    assert result.report_backend_saved is True
    assert result.rag_used is True
    assert result.rag_error is None
    assert backend.reports[0]["source"] == "kws_rag"
    assert backend.reports[0]["report"] == "# 비상정지 보고서"


def test_kws_rag_failure_is_reported_without_losing_stop_event() -> None:
    backend = FakeBackendClient()
    service = KwsService(
        backend_client=backend,
        rag_engine=FailingRagEngine(),
    )

    result = service.simulate(
        SimulateKwsRequest(text="멈춰", call_rag=True)
    )

    assert result.backend_saved is True
    assert result.stop_command.accepted is True
    assert result.rag_used is False
    assert result.report_backend_saved is False
    assert result.rag_error == "RAG index unavailable"
