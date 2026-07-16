from fastapi import APIRouter, HTTPException

from app.services.vision_llm.rag.engine import get_engine
from app.services.vision_llm.rag.schemas import (
    ReportRequest,
    ReportResponse,
    SearchRequest,
    SearchResponse,
)


router = APIRouter(prefix="/rag", tags=["vision-llm-rag"])


def _engine_or_503():
    try:
        return get_engine()
    except (FileNotFoundError, ModuleNotFoundError, RuntimeError) as exc:
        raise HTTPException(status_code=503, detail=f"RAG 엔진을 불러올 수 없습니다: {exc}") from exc


@router.get("/health")
def rag_health() -> dict:
    engine = _engine_or_503()
    return {
        "status": "ok",
        "indexes": {route: len(rows) for route, rows in engine.metadata.items()},
    }


@router.post("/search", response_model=SearchResponse)
def rag_search(request: SearchRequest) -> SearchResponse:
    return _engine_or_503().search(
        event=request.event.to_search_dict(),
        route=request.route,
        top_k=request.top_k,
        candidate_multiplier=request.candidate_multiplier,
    )


@router.post("/report", response_model=ReportResponse)
def rag_report(request: ReportRequest) -> ReportResponse:
    return _engine_or_503().build_report_basis(
        event=request.event.to_search_dict(),
        route=request.route,
        top_k=request.top_k,
        candidate_multiplier=request.candidate_multiplier,
        include_markdown=request.include_markdown,
    )
