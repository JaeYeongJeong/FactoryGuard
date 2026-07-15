import os
from dotenv import load_dotenv
from openai import OpenAI
import base64
from pathlib import Path

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def encode_image(image_path):
    """이미지를 Base64로 변환"""
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def analyze_accident(image_path):
    """Vision LLM을 이용한 사고 상황 분석"""

    base64_image = encode_image(image_path)

    response = client.chat.completions.create(
        model="gpt-4.1",
        messages=[
            {
                "role": "system",
                "content": """
당신은 산업안전 전문가입니다.

제공된 이미지를 분석하여
사고 상황을 객관적으로 판단하고
아래 형식으로 보고서를 작성하세요.

출력 형식

■ 사고 개요

■ 현재 관찰된 상황

■ 추정 사고 유형

■ 위험도
(상 / 중 / 하)

■ 즉시 필요한 조치

■ 추가 확인 사항

이미지에서 확인 가능한 사실만 작성하고
불확실한 내용은 "추정"이라고 명시하세요.
"""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "이미지를 분석하여 산업재해 사고 보고서를 작성하세요."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]
    )

    return response.choices[0].message.content


if __name__ == "__main__":

    image_path = "./data/accident4.png"

    report = analyze_accident(image_path)

    print("=" * 80)
    print(report)