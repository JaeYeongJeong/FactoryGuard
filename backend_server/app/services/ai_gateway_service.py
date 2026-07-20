from __future__ import annotations

from typing import Any

import httpx

from app.config import AI_SERVER_TIMEOUT, AI_SERVER_URL


class AIServiceError(Exception):
    def __init__(self, status_code: int, detail: Any) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class AIGatewayService:
    def __init__(
        self,
        base_url: str = AI_SERVER_URL,
        timeout: float = AI_SERVER_TIMEOUT,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._transport = transport

    async def _request(
        self,
        method: str,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        files: dict[str, tuple[str, bytes, str]] | None = None,
        params: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient(
                base_url=self._base_url,
                timeout=self._timeout,
                transport=self._transport,
            ) as client:
                response = await client.request(
                    method,
                    path,
                    json=json,
                    files=files,
                    params=params,
                )
        except httpx.TimeoutException as exc:
            raise AIServiceError(504, "AI 서버 응답 시간이 초과되었습니다.") from exc
        except httpx.RequestError as exc:
            raise AIServiceError(502, "AI 서버에 연결할 수 없습니다.") from exc

        if response.is_error:
            try:
                detail = response.json().get("detail")
            except (ValueError, AttributeError):
                detail = None
            raise AIServiceError(
                response.status_code,
                detail or "AI 서버 요청을 처리하지 못했습니다.",
            )
        return response.json()

    async def get(self, path: str) -> dict[str, Any]:
        return await self._request("GET", path)

    async def post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", path, json=payload)

    async def analyze_image(
        self,
        path: str,
        filename: str,
        content: bytes,
        content_type: str,
        event_id: str | None = None,
    ) -> dict[str, Any]:
        params = {"event_id": event_id} if event_id else None
        return await self._request(
            "POST",
            path,
            files={"image": (filename, content, content_type)},
            params=params,
        )


ai_gateway_service = AIGatewayService()
