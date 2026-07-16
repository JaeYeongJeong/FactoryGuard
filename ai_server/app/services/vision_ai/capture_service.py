"""위험 감지 프레임을 로컬 capture 폴더에 저장합니다."""

import re
from datetime import datetime
from pathlib import Path
from typing import Iterable

import cv2
import numpy as np
from loguru import logger


class CaptureService:
    """최초 위험 감지 이벤트의 처리 프레임을 JPEG로 저장합니다."""

    def __init__(self, capture_dir: str, enabled: bool = True) -> None:
        self._capture_dir = self._resolve_capture_dir(capture_dir)
        self._enabled = enabled
        if enabled:
            self._capture_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def _resolve_capture_dir(capture_dir: str) -> Path:
        path = Path(capture_dir).expanduser()
        if path.is_absolute():
            return path

        ai_server_root = Path(__file__).resolve().parents[3]
        if path.parts and path.parts[0] == ai_server_root.name:
            path = Path(*path.parts[1:])
        return ai_server_root / path

    @property
    def capture_dir(self) -> Path:
        return self._capture_dir

    @staticmethod
    def _safe_name(value) -> str:
        return re.sub(r"[^A-Za-z0-9_.-]+", "-", str(value)).strip("-") or "unknown"

    def save_danger_frames(
        self,
        frame: np.ndarray,
        events: Iterable,
        camera_id: str,
    ) -> list[Path]:
        if not self._enabled:
            return []

        saved_paths = []
        for event in events:
            event_type = getattr(event.event_type, "value", event.event_type)
            if event_type != "entered":
                continue

            occurred_at = datetime.fromtimestamp(event.timestamp)
            timestamp = occurred_at.strftime("%Y%m%d_%H%M%S_%f")[:-3]
            filename = "_".join(
                [
                    timestamp,
                    self._safe_name(camera_id),
                    self._safe_name(event.threat_type),
                    f"worker-{self._safe_name(event.tracker_id)}",
                    self._safe_name(event.zone_id),
                ]
            ) + ".jpg"
            capture_path = self._capture_dir / filename

            try:
                if not cv2.imwrite(str(capture_path), frame):
                    logger.warning(f"위험 감지 프레임 저장 실패: {capture_path}")
                    continue
            except Exception as exc:
                logger.warning(f"위험 감지 프레임 저장 오류 ({capture_path}): {exc}")
                continue

            saved_paths.append(capture_path)
            logger.info(f"위험 감지 프레임 저장: {capture_path}")

        return saved_paths
