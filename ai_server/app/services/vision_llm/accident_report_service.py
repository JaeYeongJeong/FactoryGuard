import base64
from functools import lru_cache
from pathlib import Path
from uuid import uuid4

from openai import OpenAI

from app.config import settings
from app.services.vision_llm.rag.engine import get_engine


@lru_cache(maxsize=1)
def get_openai_client() -> OpenAI:
    api_key = settings.api.openai_api_key
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
    return OpenAI(api_key=api_key)


def encode_image(image_path: str | Path) -> str:
    """이미지를 Base64 문자열로 변환합니다."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def analyze_accident(
    image_path: str | Path,
    mime_type: str = "image/jpeg",
) -> str:
    """Vision LLM을 이용해 산업재해 사고 상황을 분석합니다."""

    base64_image = encode_image(image_path)

    response = get_openai_client().chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": """
당신은 산업안전 전문가입니다.

제공된 이미지를 분석하여 사고 상황을 객관적으로 판단하고
아래 형식으로 보고서를 작성하세요.

■ 사고 개요

■ 현재 관찰된 상황

■ 추정 사고 유형

■ 위험도
(상 / 중 / 하)

■ 즉시 필요한 조치

■ 추가 확인 사항

이미지에서 확인 가능한 사실만 작성하고,
불확실한 내용은 "추정"이라고 명시하세요.
""",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "이미지를 분석하여 산업재해 사고 보고서를 작성하세요.",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": (
                                f"data:{mime_type};base64,"
                                f"{base64_image}"
                            )
                        },
                    },
                ],
            },
        ],
    )

    report = response.choices[0].message.content

    if not report:
        raise RuntimeError("사고 분석 결과가 비어 있습니다.")

    return report


def generate_report_with_legal_basis(
    image_path: str | Path,
    mime_type: str = "image/jpeg",
    event_id: str | None = None,
) -> dict:
    """Vision 분석 결과에 RAG 법령 근거와 권장 조치를 결합합니다."""

    report = analyze_accident(image_path, mime_type)
    linked_event_id = event_id or f"report-event-{uuid4().hex}"
    rag_event = {
        "event_id": linked_event_id,
        "source": "vision",
        "risk_type": "산업재해 위험",
        "description": report,
        "vision_labels": ["vision_llm_accident_analysis"],
    }

    try:
        rag_result = get_engine().build_report_basis(
            event=rag_event,
            top_k=settings.rag.top_k,
            include_markdown=True,
        )
    except Exception as exc:
        return {
            "event_id": linked_event_id,
            "report": report,
            "legal_basis": [],
            "recommended_action": [],
            "rag_available": False,
            "rag_error": str(exc),
            "rag_markdown": None,
        }

    return {
        "event_id": linked_event_id,
        "report": report,
        "legal_basis": [item.model_dump() for item in rag_result.legal_basis],
        "recommended_action": rag_result.recommended_action,
        "rag_available": True,
        "rag_error": None,
        "rag_markdown": rag_result.markdown,
    }
