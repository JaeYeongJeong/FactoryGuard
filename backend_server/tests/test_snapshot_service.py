import asyncio
import os

os.environ.setdefault("MONGODB_URI", "mongodb://localhost:27017")

import httpx
import pytest

from app.services.snapshot_service import SnapshotError, SnapshotService


def test_snapshot_is_loaded_only_from_configured_capture_base() -> None:
    async def handler(request: httpx.Request) -> httpx.Response:
        assert str(request.url) == "https://ai.example.com/captures/danger.jpg"
        return httpx.Response(
            200,
            content=b"jpeg-data",
            headers={"content-type": "image/jpeg"},
        )

    service = SnapshotService(
        capture_base_url="https://ai.example.com/captures",
        transport=httpx.MockTransport(handler),
    )

    result = asyncio.run(
        service.fetch("https://ai.example.com/captures/danger.jpg")
    )

    assert result == ("danger.jpg", b"jpeg-data", "image/jpeg")


def test_snapshot_outside_configured_capture_base_is_rejected() -> None:
    service = SnapshotService(
        capture_base_url="https://ai.example.com/captures",
    )

    with pytest.raises(SnapshotError, match="허용되지 않은"):
        asyncio.run(service.fetch("https://other.example.com/private.jpg"))

    with pytest.raises(SnapshotError, match="허용되지 않은"):
        asyncio.run(
            service.fetch(
                "https://ai.example.com/captures/%2E%2E/private.jpg"
            )
        )
