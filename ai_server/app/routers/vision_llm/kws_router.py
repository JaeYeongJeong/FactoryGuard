from fastapi import APIRouter, HTTPException

from app.services.vision_llm.kws.actuator import get_actuator
from app.services.vision_llm.kws.config import get_settings
from app.services.vision_llm.kws.schemas import (
    SimulateKwsRequest,
    SimulateKwsResponse,
    StopCommandResult,
    StopTestRequest,
)
from app.services.vision_llm.kws.service import get_kws_service


router = APIRouter(prefix="/kws", tags=["vision-llm-kws"])


@router.get("/health")
def kws_health() -> dict:
    config = get_settings()
    return {
        "status": "ok",
        "detector": "simulation",
        "threshold": config.threshold,
        "cooldown_seconds": config.cooldown_seconds,
        "actuator_mode": config.actuator_mode,
        "keywords": [item.keyword for item in config.keywords],
    }


@router.post("/simulate", response_model=SimulateKwsResponse)
def simulate_kws(request: SimulateKwsRequest) -> SimulateKwsResponse:
    return get_kws_service().simulate(request)


@router.post("/stop-test", response_model=StopCommandResult)
def stop_test(request: StopTestRequest) -> StopCommandResult:
    try:
        return get_actuator(get_settings().actuator_mode).stop(
            None,
            reason=request.reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
