from __future__ import annotations

from functools import lru_cache
import logging
from typing import Any

from app.config import settings as app_settings
from app.services.vision_llm.communication.backend_client import BackendClient
from app.services.vision_llm.kws.actuator import get_actuator
from app.services.vision_llm.kws.config import get_settings
from app.services.vision_llm.kws.detector import SimulationKeywordDetector
from app.services.vision_llm.kws.event_builder import build_kws_event
from app.services.vision_llm.kws.schemas import SimulateKwsRequest, SimulateKwsResponse


logger = logging.getLogger(__name__)


class KwsService:
    def __init__(
        self,
        backend_client: BackendClient | None = None,
    ) -> None:
        self.settings = get_settings()
        self.detector = SimulationKeywordDetector(self.settings)
        self.backend_client = backend_client or BackendClient(
            app_settings.api.backend_url,
            timeout=app_settings.api.timeout,
        )

    @staticmethod
    def _backend_event(event, line_id: str | None) -> dict[str, Any]:
        return {
            "event_id": event.event_id,
            "camera_id": line_id or "kws-microphone",
            "timestamp": event.timestamp,
            "event_type": "kws_emergency_stop",
            "severity": "critical",
            "status": "entered",
            "worker_id": 0,
            "zone_name": event.location,
            "message": event.description,
            "snapshot_url": None,
        }

    def simulate(self, request: SimulateKwsRequest) -> SimulateKwsResponse:
        detection = self.detector.detect_text(request.text)
        if not detection.detected:
            return SimulateKwsResponse(detection=detection)

        event = build_kws_event(
            detection,
            self.settings,
            location=request.location,
            equipment=request.equipment,
            line_id=request.line_id,
        )
        stop_result = None
        if request.force_stop:
            stop_result = get_actuator(self.settings.actuator_mode).stop(
                event,
                reason="kws_detected",
            )

        backend_event = self._backend_event(event, request.line_id)
        backend_saved = False
        try:
            self.backend_client.create_event(backend_event)
            backend_saved = True
        except Exception as exc:
            # 설비 정지 판단은 백엔드 또는 RAG 장애에 의존하지 않습니다.
            logger.warning("KWS 이벤트 백엔드 저장 실패: %s", exc)
            backend_saved = False

        return SimulateKwsResponse(
            detection=detection,
            event=event,
            stop_command=stop_result,
            backend_saved=backend_saved,
            backend_event=backend_event,
        )


@lru_cache(maxsize=1)
def get_kws_service() -> KwsService:
    return KwsService()
