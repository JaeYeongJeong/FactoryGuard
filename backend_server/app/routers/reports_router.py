from fastapi import APIRouter, HTTPException, Query
from pymongo.errors import PyMongoError

from app.schemas.report_schema import IncidentReportCreate
from app.services.report_service import report_service


router = APIRouter(prefix="/reports", tags=["reports"])


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
