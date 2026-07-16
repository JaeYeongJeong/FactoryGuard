import base64
import os
from pathlib import Path

from openai import OpenAI

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

    response = client.chat.completions.create(
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