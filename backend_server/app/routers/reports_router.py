from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from pymongo.errors import PyMongoError

from app.schemas.report_schema import IncidentReportCreate
from app.services.ai_gateway_service import AIServiceError, ai_gateway_service
from app.services.report_service import report_service


router = APIRouter(prefix="/reports", tags=["reports"])
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024


async def _proxy_analysis(
    path: str,
    image: UploadFile,
    event_id: str | None,
):
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="JPEG, PNG, WEBP 형식의 이미지만 업로드할 수 있습니다.",
        )
    content = await image.read()
    if not content:
        raise HTTPException(
            status_code=400,
            detail="업로드된 이미지가 비어 있습니다.",
        )
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="이미지 크기는 10MB 이하여야 합니다.",
        )

    try:
        return await ai_gateway_service.analyze_image(
            path=path,
            filename=image.filename or "image.jpg",
            content=content,
            content_type=image.content_type,
            event_id=event_id,
        )
    except AIServiceError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.detail) from exc


@router.post("/analyze")
async def analyze_report(
    image: UploadFile = File(...),
    event_id: str | None = None,
):
    return await _proxy_analysis("/reports/analyze", image, event_id)


@router.post("/analyze-with-legal-basis")
async def analyze_report_with_legal_basis(
    image: UploadFile = File(...),
    event_id: str | None = None,
):
    return await _proxy_analysis(
        "/reports/analyze-with-legal-basis",
        image,
        event_id,
    )


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
