"""프론트엔드 위험 이벤트 WebSocket 연결을 관리합니다."""

import asyncio

from fastapi import WebSocket


class EventConnectionManager:
    def __init__(self) -> None:
        self._connections: set[WebSocket] = set()
        self._broadcast_lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.add(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        self._connections.discard(websocket)

    async def broadcast(self, event: dict) -> None:
        async with self._broadcast_lock:
            disconnected = []
            for websocket in list(self._connections):
                try:
                    await websocket.send_json(event)
                except Exception:
                    disconnected.append(websocket)

            for websocket in disconnected:
                self.disconnect(websocket)

    @property
    def connection_count(self) -> int:
        return len(self._connections)


event_connection_manager = EventConnectionManager()
