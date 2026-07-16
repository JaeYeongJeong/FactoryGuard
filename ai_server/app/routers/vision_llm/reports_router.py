import os
import tempfile
from datetime import datetime, timezone
import logging
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.config import settings
from app.services.vision_llm.accident_report_service import (
    analyze_accident,
    generate_report_with_legal_basis,
)
from app.services.vision_llm.communication.backend_client import BackendClient


router = APIRouter(prefix="/reports", tags=["vision-llm-reports"])
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 10 * 1024 * 1024
logger = logging.getLogger(__name__)


def _save_upload(image: UploadFile, image_bytes: bytes) -> str:
    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="JPEG, PNG, WEBP 형식의 이미지만 업로드할 수 있습니다.",
        )
    if not image_bytes:
        raise HTTPException(status_code=400, detail="업로드된 이미지가 비어 있습니다.")
    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="이미지 크기는 10MB 이하여야 합니다.")

    suffix = Path(image.filename or "image.jpg").suffix or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(image_bytes)
        return temp_file.name


def _persist_report(payload: dict) -> bool:
    try:
        BackendClient(
            settings.api.backend_url,
            timeout=settings.api.timeout,
        ).create_report(payload)
        return True
    except Exception as exc:
        logger.warning("사고 보고서 백엔드 저장 실패: %s", exc)
        return False


async def _prepare_upload(image: UploadFile) -> str:
    return _save_upload(image, await image.read())


@router.post("/analyze")
async def analyze_accident_report(
    image: UploadFile = File(...),
    event_id: str | None = None,
):
    temp_path = None
    try:
        temp_path = await _prepare_upload(image)
        report = await run_in_threadpool(
            analyze_accident,
            temp_path,
            image.content_type,
        )
        report_id = f"report-{uuid4().hex}"
        backend_saved = await run_in_threadpool(
            _persist_report,
            {
                "report_id": report_id,
                "event_id": event_id,
                "source": "vision_llm",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "report": report,
                "legal_basis": [],
                "recommended_action": [],
                "rag_available": False,
                "metadata": {"filename": image.filename},
            },
        )
        return {
            "success": True,
            "report_id": report_id,
            "event_id": event_id,
            "filename": image.filename,
            "report": report,
            "backend_saved": backend_saved,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="사고 이미지 분석 중 오류가 발생했습니다.",
        ) from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


@router.post("/analyze-with-legal-basis")
async def analyze_accident_report_with_legal_basis(
    image: UploadFile = File(...),
    event_id: str | None = None,
):
    temp_path = None
    try:
        temp_path = await _prepare_upload(image)
        result = await run_in_threadpool(
            generate_report_with_legal_basis,
            temp_path,
            image.content_type,
            event_id,
        )
        report_id = f"report-{uuid4().hex}"
        backend_saved = await run_in_threadpool(
            _persist_report,
            {
                "report_id": report_id,
                "event_id": result["event_id"],
                "source": "vision_llm_rag",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "report": result["report"],
                "legal_basis": result["legal_basis"],
                "recommended_action": result["recommended_action"],
                "rag_available": result["rag_available"],
                "metadata": {
                    "filename": image.filename,
                    "rag_error": result["rag_error"],
                    "rag_markdown": result["rag_markdown"],
                },
            },
        )
        return {
            "success": True,
            "report_id": report_id,
            "filename": image.filename,
            **result,
            "backend_saved": backend_saved,
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="사고 이미지 분석 중 오류가 발생했습니다.",
        ) from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)
