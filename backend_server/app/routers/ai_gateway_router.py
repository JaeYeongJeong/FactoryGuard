from collections.abc import Awaitable
from typing import Any

from fastapi import APIRouter, HTTPException

from app.schemas.ai_gateway_schema import (
    KwsSimulateRequest,
    KwsStopTestRequest,
    RagReportRequest,
    RagSearchRequest,
)
from app.services.ai_gateway_service import AIServiceError, ai_gateway_service


router = APIRouter(tags=["ai-gateway"])


async def _proxy(request: Awaitable[dict[str, Any]]) -> dict[str, Any]:
    try:
        return await request
    except AIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.get("/rag/health")
async def rag_health():
    return await _proxy(ai_gateway_service.get("/rag/health"))


@router.post("/rag/search")
async def rag_search(request: RagSearchRequest):
    return await _proxy(
        ai_gateway_service.post_json("/rag/search", request.model_dump(mode="json"))
    )


@router.post("/rag/report")
async def rag_report(request: RagReportRequest):
    return await _proxy(
        ai_gateway_service.post_json("/rag/report", request.model_dump(mode="json"))
    )


@router.get("/kws/health")
async def kws_health():
    return await _proxy(ai_gateway_service.get("/kws/health"))


@router.post("/kws/simulate")
async def kws_simulate(request: KwsSimulateRequest):
    return await _proxy(
        ai_gateway_service.post_json("/kws/simulate", request.model_dump(mode="json"))
    )


@router.post("/kws/stop-test")
async def kws_stop_test(request: KwsStopTestRequest):
    return await _proxy(
        ai_gateway_service.post_json("/kws/stop-test", request.model_dump(mode="json"))
    )
