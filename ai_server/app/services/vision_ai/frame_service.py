"""WebSocket 프레임과 비전 처리 파이프라인을 연결하는 서비스."""

from typing import Optional, Protocol

import cv2
import numpy as np
from loguru import logger

from app.services.vision_ai.capture_service import CaptureService
from app.services.vision_ai.communication.event_publisher import EventPublisher


class FrameProcessor(Protocol):
    def process(
        self,
        frame: np.ndarray,
        show_display: bool = True,
    ) -> tuple[np.ndarray, list]: ...


class FrameService:
    """JPEG 디코딩, 위험 감지 파이프라인 실행, JPEG 인코딩을 담당합니다."""

    def __init__(
        self,
        processor: FrameProcessor,
        jpeg_quality: int = 75,
        resize: Optional[tuple[int, int]] = None,
        capture_service: Optional[CaptureService] = None,
        event_publisher: Optional[EventPublisher] = None,
    ) -> None:
        self._processor = processor
        self._jpeg_quality = jpeg_quality
        self._resize = resize
        self._capture_service = capture_service
        self._event_publisher = event_publisher

    @staticmethod
    def decode_frame(frame_bytes: bytes) -> Optional[np.ndarray]:
        if not frame_bytes:
            return None

        frame_array = np.frombuffer(frame_bytes, dtype=np.uint8)
        return cv2.imdecode(frame_array, cv2.IMREAD_COLOR)

    def encode_frame(self, frame: np.ndarray) -> Optional[bytes]:
        success, encoded = cv2.imencode(
            ".jpg",
            frame,
            [cv2.IMWRITE_JPEG_QUALITY, self._jpeg_quality],
        )
        if not success:
            return None
        return encoded.tobytes()

    def process_frame(
        self,
        frame_bytes: bytes,
        camera_id: str,
    ) -> tuple[Optional[bytes], list]:
        """수신 JPEG를 기존 위험 감지 파이프라인에 전달합니다."""
        frame = self.decode_frame(frame_bytes)
        if frame is None:
            logger.warning(f"JPEG 프레임 디코딩 실패: {camera_id}")
            return None, []

        if self._resize is not None:
            width, height = self._resize
            if frame.shape[1] != width or frame.shape[0] != height:
                frame = cv2.resize(frame, self._resize)

        processed_frame, events = self._processor.process(
            frame,
            show_display=True,
        )

        for event in events:
            snapshot_path = None
            if self._capture_service is not None:
                snapshot_path = self._capture_service.save_danger_frame(
                    processed_frame,
                    event,
                    camera_id,
                )
            if self._event_publisher is not None:
                self._event_publisher.publish(event, camera_id, snapshot_path)

        encoded_frame = self.encode_frame(processed_frame)
        if encoded_frame is None:
            logger.warning(f"처리 프레임 JPEG 인코딩 실패: {camera_id}")
            return None, events

        return encoded_frame, events
