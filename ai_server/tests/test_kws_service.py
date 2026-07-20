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
    assert backend.reports == []
