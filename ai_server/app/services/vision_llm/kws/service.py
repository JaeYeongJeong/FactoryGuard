from __future__ import annotations

from functools import lru_cache
import logging
from typing import Any
from uuid import uuid4

from app.config import settings as app_settings
from app.services.vision_llm.communication.backend_client import BackendClient
from app.services.vision_llm.kws.actuator import get_actuator
from app.services.vision_llm.kws.config import get_settings
from app.services.vision_llm.kws.detector import SimulationKeywordDetector
from app.services.vision_llm.kws.event_builder import build_kws_event
from app.services.vision_llm.kws.schemas import SimulateKwsRequest, SimulateKwsResponse
from app.services.vision_llm.rag.engine import RagEngine, get_engine


logger = logging.getLogger(__name__)


class KwsService:
    def __init__(
        self,
        backend_client: BackendClient | None = None,
        rag_engine: RagEngine | None = None,
    ) -> None:
        self.settings = get_settings()
        self.detector = SimulationKeywordDetector(self.settings)
        self.backend_client = backend_client or BackendClient(
            app_settings.api.backend_url,
            timeout=app_settings.api.timeout,
        )
        self._rag_engine = rag_engine

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

        rag_report = None
        rag_used = False
        rag_error = None
        report_backend_saved = False
        if request.call_rag:
            try:
                engine = self._rag_engine or get_engine()
                rag_event = event.model_dump()
                rag_event["hazard_tags"] = ["비상정지"]
                rag_report = engine.build_report_basis(
                    event=rag_event,
                    route="safety",
                    top_k=app_settings.rag.top_k,
                    include_markdown=True,
                ).model_dump()
                rag_used = True
            except Exception as exc:
                rag_error = str(exc)
                logger.exception("KWS RAG 근거 생성 실패: %s", exc)

            if rag_report is not None:
                try:
                    self.backend_client.create_report(
                        {
                            "report_id": f"report-{uuid4().hex}",
                            "event_id": event.event_id,
                            "source": "kws_rag",
                            "created_at": event.timestamp,
                            "report": (
                                rag_report.get("markdown")
                                or event.description
                            ),
                            "legal_basis": rag_report.get("legal_basis", []),
                            "recommended_action": rag_report.get(
                                "recommended_action",
                                [],
                            ),
                            "rag_available": True,
                            "metadata": {
                                "kws_event": event.model_dump(),
                                "rag_route": rag_report.get("route"),
                            },
                        }
                    )
                    report_backend_saved = True
                except Exception as exc:
                    rag_error = f"RAG 생성 성공, 백엔드 저장 실패: {exc}"
                    logger.warning("KWS RAG 보고서 백엔드 저장 실패: %s", exc)

        return SimulateKwsResponse(
            detection=detection,
            event=event,
            stop_command=stop_result,
            rag_report=rag_report,
            rag_used=rag_used,
            rag_error=rag_error,
            backend_saved=backend_saved,
            backend_event=backend_event,
            report_backend_saved=report_backend_saved,
        )


@lru_cache(maxsize=1)
def get_kws_service() -> KwsService:
    return KwsService()
