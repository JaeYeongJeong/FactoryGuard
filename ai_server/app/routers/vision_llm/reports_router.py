import os
import tempfile
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
from starlette.concurrency import run_in_threadpool

from app.services.vision_llm.accident_report_service import analyze_accident


router = APIRouter(
    prefix="/reports",
    tags=["reports"],
)


ALLOWED_IMAGE_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
}

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


@router.post("/analyze")
async def analyze_accident_report(
    image: UploadFile = File(...),
):
    """
    사고 이미지를 업로드받아 Vision LLM으로 분석합니다.
    """

    if image.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status_code=400,
            detail="JPEG, PNG, WEBP 형식의 이미지만 업로드할 수 있습니다.",
        )

    image_bytes = await image.read()

    if not image_bytes:
        raise HTTPException(
            status_code=400,
            detail="업로드된 이미지가 비어 있습니다.",
        )

    if len(image_bytes) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="이미지 크기는 10MB 이하여야 합니다.",
        )

    suffix = Path(image.filename or "image.jpg").suffix

    if not suffix:
        suffix = ".jpg"

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=suffix,
        ) as temp_file:
            temp_file.write(image_bytes)
            temp_path = temp_file.name

        report = await run_in_threadpool(
            analyze_accident,
            temp_path,
            image.content_type,
        )

        return {
            "success": True,
            "filename": image.filename,
            "report": report,
        }

    except HTTPException:
        raise

    except Exception as exc:
        print(f"[accident-report] error: {exc}")

        raise HTTPException(
            status_code=500,
            detail="사고 이미지 분석 중 오류가 발생했습니다.",
        ) from exc

    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)