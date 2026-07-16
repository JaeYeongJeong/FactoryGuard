from __future__ import annotations

from typing import Any

import httpx


class BackendClient:
    def __init__(self, base_url: str, timeout: float = 5.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout

    def _post(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        response = httpx.post(
            f"{self._base_url}{path}",
            json=payload,
            timeout=self._timeout,
        )
        response.raise_for_status()
        return response.json()

    def create_event(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/events/detect", payload)

    def create_report(self, payload: dict[str, Any]) -> dict[str, Any]:
        return self._post("/reports", payload)
