import asyncio
import json
import os

import httpx
import pytest

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")

from app.services.ai_gateway_service import AIGatewayService, AIServiceError


def test_json_request_is_forwarded_to_ai_server() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/rag/search"
        payload = json.loads(request.content)
        assert payload["event"]["risk_type"] == "끼임"
        return httpx.Response(200, json={"route": "safety", "results": []})

    service = AIGatewayService(
        base_url="http://ai-server:8001",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.post_json(
            "/rag/search",
            {"event": {"risk_type": "끼임"}},
        )
    )

    assert result == {"route": "safety", "results": []}


def test_image_and_event_id_are_forwarded() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/reports/analyze"
        assert request.url.params["event_id"] == "event-001"
        assert b'filename="accident.jpg"' in request.content
        assert b"jpeg-data" in request.content
        return httpx.Response(200, json={"success": True, "report_id": "report-001"})

    service = AIGatewayService(
        base_url="http://ai-server:8001",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.analyze_image(
            path="/reports/analyze",
            filename="accident.jpg",
            content=b"jpeg-data",
            content_type="image/jpeg",
            event_id="event-001",
        )
    )

    assert result["report_id"] == "report-001"


def test_ai_connection_failure_becomes_bad_gateway() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    service = AIGatewayService(
        base_url="http://ai-server:8001",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AIServiceError) as exc_info:
        asyncio.run(service.get("/rag/health"))

    assert exc_info.value.status_code == 502
    assert exc_info.value.detail == "AI 서버에 연결할 수 없습니다."


def test_ai_timeout_becomes_gateway_timeout() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("timed out", request=request)

    service = AIGatewayService(
        base_url="http://ai-server:8001",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AIServiceError) as exc_info:
        asyncio.run(service.get("/rag/health"))

    assert exc_info.value.status_code == 504
    assert exc_info.value.detail == "AI 서버 응답 시간이 초과되었습니다."


def test_ai_validation_error_is_preserved() -> None:
    async def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(422, json={"detail": "잘못된 요청입니다."})

    service = AIGatewayService(
        base_url="http://ai-server:8001",
        transport=httpx.MockTransport(handler),
    )

    with pytest.raises(AIServiceError) as exc_info:
        asyncio.run(service.post_json("/kws/simulate", {"text": ""}))

    assert exc_info.value.status_code == 422
    assert exc_info.value.detail == "잘못된 요청입니다."
