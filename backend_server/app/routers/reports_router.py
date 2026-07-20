from fastapi import APIRouter, HTTPException, Query
from pymongo.errors import PyMongoError

from app.schemas.report_schema import (
    IncidentReportAnalysisRequest,
    IncidentReportCreate,
)
from app.services.ai_gateway_service import AIServiceError, ai_gateway_service
from app.services.report_service import report_service
from app.services.event_service import event_service
from app.services.snapshot_service import SnapshotError, snapshot_service


router = APIRouter(prefix="/reports", tags=["reports"])
@router.post("/analyze-event/{event_id}")
async def analyze_event_report(
    event_id: str,
    request: IncidentReportAnalysisRequest,
):
    try:
        event = await event_service.get_event(event_id)
    except PyMongoError as exc:
        raise HTTPException(
            status_code=503,
            detail="이벤트 저장소에 연결할 수 없습니다.",
        ) from exc
    if event is None:
        raise HTTPException(status_code=404, detail="이벤트를 찾을 수 없습니다.")

    snapshot_url = event.get("snapshot_url")
    if not snapshot_url:
        raise HTTPException(
            status_code=422,
            detail="이 이벤트에는 분석할 캡처 이미지가 없습니다.",
        )

    try:
        filename, content, content_type = await snapshot_service.fetch(snapshot_url)
    except SnapshotError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc

    try:
        return await ai_gateway_service.analyze_image(
            path=(
                "/reports/analyze-with-legal-basis"
                if request.use_rag
                else "/reports/analyze"
            ),
            filename=filename,
            content=content,
            content_type=content_type,
            event_id=event_id,
        )
    except AIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("")
async def create_report(report: IncidentReportCreate):
    try:
        return {"success": True, "report": await report_service.create_report(report)}
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail="리포트 저장소에 연결할 수 없습니다.") from exc


@router.get("")
async def list_reports(limit: int = Query(default=50, ge=1, le=200)):
    try:
        return {"reports": await report_service.list_reports(limit)}
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail="리포트 저장소에 연결할 수 없습니다.") from exc


@router.get("/{report_id}")
async def get_report(report_id: str):
    try:
        report = await report_service.get_report(report_id)
    except PyMongoError as exc:
        raise HTTPException(status_code=503, detail="리포트 저장소에 연결할 수 없습니다.") from exc
    if report is None:
        raise HTTPException(status_code=404, detail="리포트를 찾을 수 없습니다.")
    return {"report": report}
