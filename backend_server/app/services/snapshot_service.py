from pathlib import PurePosixPath
from urllib.parse import unquote, urlparse

import httpx

from app.config import AI_SERVER_TIMEOUT, CAPTURE_BASE_URL


class SnapshotError(Exception):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


class SnapshotService:
    ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
    MAX_FILE_SIZE = 10 * 1024 * 1024

    def __init__(
        self,
        capture_base_url: str = CAPTURE_BASE_URL,
        timeout: float = AI_SERVER_TIMEOUT,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._capture_base_url = capture_base_url.rstrip("/")
        self._capture_base = urlparse(self._capture_base_url)
        self._timeout = timeout
        self._transport = transport

    async def fetch(self, snapshot_url: str) -> tuple[str, bytes, str]:
        parsed_url = urlparse(snapshot_url)
        decoded_path = unquote(parsed_url.path)
        allowed_path = f"{self._capture_base.path.rstrip('/')}/"
        if (
            parsed_url.scheme != self._capture_base.scheme
            or parsed_url.netloc != self._capture_base.netloc
            or not decoded_path.startswith(allowed_path)
            or ".." in PurePosixPath(decoded_path).parts
        ):
            raise SnapshotError(400, "허용되지 않은 캡처 이미지 주소입니다.")

        try:
            async with httpx.AsyncClient(
                timeout=self._timeout,
                transport=self._transport,
                follow_redirects=False,
            ) as client:
                response = await client.get(snapshot_url)
        except httpx.TimeoutException as exc:
            raise SnapshotError(504, "캡처 이미지 조회 시간이 초과되었습니다.") from exc
        except httpx.RequestError as exc:
            raise SnapshotError(502, "AI 캡처 서버에 연결할 수 없습니다.") from exc

        if response.is_error:
            raise SnapshotError(502, "캡처 이미지를 가져오지 못했습니다.")

        content_type = response.headers.get("content-type", "").split(";", 1)[0]
        if content_type not in self.ALLOWED_TYPES:
            raise SnapshotError(400, "지원하지 않는 캡처 이미지 형식입니다.")
        if not response.content:
            raise SnapshotError(400, "캡처 이미지가 비어 있습니다.")
        if len(response.content) > self.MAX_FILE_SIZE:
            raise SnapshotError(413, "캡처 이미지는 10MB 이하여야 합니다.")

        filename = PurePosixPath(decoded_path).name
        return filename or "capture.jpg", response.content, content_type


snapshot_service = SnapshotService()
