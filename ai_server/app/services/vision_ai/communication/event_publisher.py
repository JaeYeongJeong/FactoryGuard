"""위험 감지 이벤트를 백엔드 API로 비동기 전송합니다."""

import queue
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote
from uuid import uuid4

import httpx
from loguru import logger


class EventPublisher:
    """추론 루프와 분리된 큐에서 위험 이벤트를 백엔드로 전송합니다."""

    def __init__(
        self,
        backend_url: str,
        ai_public_url: str,
        capture_base_url: Optional[str] = None,
        timeout: float = 5.0,
        retry_count: int = 3,
        max_queue_size: int = 200,
    ) -> None:
        self._endpoint = f"{backend_url.rstrip('/')}/events/detect"
        self._capture_base_url = (
            capture_base_url.rstrip("/")
            if capture_base_url
            else f"{ai_public_url.rstrip('/')}/captures"
        )
        self._timeout = timeout
        self._retry_count = retry_count
        self._queue: queue.Queue[dict] = queue.Queue(maxsize=max_queue_size)
        self._running = False
        self._worker: Optional[threading.Thread] = None

    @staticmethod
    def _message(event) -> str:
        worker = f"작업자 {event.tracker_id}"
        threat_names = {
            "intrusion": f"위험구역 {event.zone_name} 침입",
            "gesture_x": "양팔 교차 위험 신호",
            "gesture_wave": "도움 요청 손 흔들기",
            "fall_down": "쓰러짐",
        }
        threat = threat_names.get(event.threat_type, "위험 상황")
        status = getattr(event.event_type, "value", event.event_type)
        if status == "exited":
            return f"{worker}의 {threat} 상태가 해제되었습니다."
        if status == "staying":
            return f"{worker}의 {threat} 상태가 지속 중입니다."
        return f"{worker}의 {threat}이 감지되었습니다."

    def build_payload(
        self,
        event,
        camera_id: str,
        snapshot_path: Optional[Path] = None,
    ) -> dict:
        snapshot_url = None
        if snapshot_path is not None:
            filename = quote(snapshot_path.name)
            snapshot_url = f"{self._capture_base_url}/{filename}"

        status = getattr(event.event_type, "value", event.event_type)
        timestamp = datetime.fromtimestamp(event.timestamp, tz=timezone.utc)
        return {
            "event_id": str(uuid4()),
            "camera_id": camera_id,
            "timestamp": timestamp.isoformat(),
            "event_type": event.threat_type,
            "severity": event.zone_severity,
            "status": status,
            "worker_id": event.tracker_id,
            "zone_name": event.zone_name,
            "message": self._message(event),
            "snapshot_url": snapshot_url,
        }

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._worker = threading.Thread(
            target=self._run,
            daemon=True,
            name="factoryguard-event-publisher",
        )
        self._worker.start()

    def publish(
        self,
        event,
        camera_id: str,
        snapshot_path: Optional[Path] = None,
    ) -> None:
        payload = self.build_payload(event, camera_id, snapshot_path)
        try:
            self._queue.put_nowait(payload)
        except queue.Full:
            logger.error(f"위험 이벤트 전송 큐가 가득 참: {payload['event_id']}")

    def _send(self, client: httpx.Client, payload: dict) -> bool:
        for attempt in range(1, self._retry_count + 1):
            try:
                response = client.post(self._endpoint, json=payload)
                response.raise_for_status()
                return True
            except httpx.HTTPError as exc:
                logger.warning(
                    f"백엔드 이벤트 전송 실패 "
                    f"({attempt}/{self._retry_count}, {payload['event_id']}): {exc}"
                )
                if attempt < self._retry_count:
                    time.sleep(min(attempt, 2))
        return False

    def _run(self) -> None:
        with httpx.Client(timeout=self._timeout) as client:
            while self._running or not self._queue.empty():
                try:
                    payload = self._queue.get(timeout=0.2)
                except queue.Empty:
                    continue

                if not self._send(client, payload):
                    logger.error(f"위험 이벤트 전송 최종 실패: {payload['event_id']}")
                self._queue.task_done()

    def stop(self) -> None:
        self._running = False
        if self._worker and self._worker.is_alive():
            self._worker.join(timeout=5)
        self._worker = None
