"""Vision AI 파이프라인 조립과 애플리케이션 수명주기를 관리합니다."""

import threading
from typing import Optional

from loguru import logger

from app.config import settings
from app.services.vision_ai import (
    DangerZoneManager,
    FrameProcessor,
    FrameRenderer,
    IntrusionDetector,
    PersonDetector,
    PersonTracker,
    create_video_source,
)
from app.services.vision_ai.capture_service import CaptureService
from app.services.vision_ai.communication.event_publisher import EventPublisher
from app.services.vision_ai.frame_service import FrameService
from app.services.vision_ai.websocket_service import websocket_service


class VisionAIService:
    """Vision AI 구성 요소와 실행 상태를 한 곳에서 관리합니다."""

    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._video_thread: Optional[threading.Thread] = None
        self._processor: Optional[FrameProcessor] = None
        self._zone_manager: Optional[DangerZoneManager] = None
        self._video_source = None
        self._event_publisher: Optional[EventPublisher] = None

    def _build_frame_processor(self, video_source=None) -> FrameProcessor:
        self._zone_manager = DangerZoneManager(
            camera_id=settings.camera_id,
            poll_interval=settings.zone.poll_interval,
            frame_width=settings.video.width,
            frame_height=settings.video.height,
            default_zones=settings.zone.default_zones,
        )
        if not settings.zone.default_zones:
            self._zone_manager.set_demo_zones(
                settings.video.width,
                settings.video.height,
            )

        detector = PersonDetector(
            model_path=settings.detector.model_path,
            confidence_threshold=settings.detector.confidence_threshold,
            iou_threshold=settings.detector.iou_threshold,
            device=settings.detector.device,
            img_size=settings.detector.img_size,
            target_classes=settings.detector.target_classes,
        )
        tracker = PersonTracker(
            track_thresh=settings.tracker.track_thresh,
            track_buffer=settings.tracker.track_buffer,
            match_thresh=settings.tracker.match_thresh,
        )
        intrusion_detector = IntrusionDetector(
            cooldown_seconds=settings.event.cooldown_seconds,
            method=settings.event.intrusion_method,
            overlap_ratio=settings.event.overlap_ratio,
            frame_width=settings.video.width,
            frame_height=settings.video.height,
            pose_conf_threshold=settings.event.pose_conf_threshold,
            waving_amplitude_ratio=settings.event.waving_amplitude_ratio,
            waving_direction_changes=settings.event.waving_direction_changes,
            waving_min_frames=settings.event.waving_min_frames,
            waving_conf_threshold=settings.event.waving_conf_threshold,
            waving_y_ratio=settings.event.waving_y_ratio,
            waving_history_frames=settings.event.waving_history_frames,
            waving_smooth_window=settings.event.waving_smooth_window,
            waving_pixel_threshold=settings.event.waving_pixel_threshold,
            waving_speed_threshold=settings.event.waving_speed_threshold,
            enter_threshold_frames=settings.event.enter_threshold_frames,
            exit_threshold_frames=settings.event.exit_threshold_frames,
        )

        return FrameProcessor(
            video_source=video_source,
            detector=detector,
            tracker=tracker,
            intrusion_detector=intrusion_detector,
            renderer=FrameRenderer(),
            zone_manager=self._zone_manager,
            event_sender=None,
            show_display=settings.show_display,
        )

    def start(self) -> None:
        if self._processor is not None:
            return

        logger.info("FactoryGuard Vision AI 파이프라인 초기화 중")
        if not settings.video.source.startswith("websocket://"):
            self._video_source = create_video_source(
                settings.video.source,
                resize=(settings.video.width, settings.video.height),
                fps_limit=settings.video.fps_limit,
                loop=settings.video.loop,
            )
            if not self._video_source.open():
                logger.error("로컬 영상 연결 실패, WebSocket 수신 모드만 활성화합니다.")
                self._video_source = None

        self._processor = self._build_frame_processor(self._video_source)
        self._event_publisher = EventPublisher(
            backend_url=settings.api.backend_url,
            ai_public_url=settings.api.ai_public_url,
            capture_base_url=settings.api.capture_base_url,
            timeout=settings.api.timeout,
            retry_count=settings.api.retry_count,
        )
        self._event_publisher.start()
        websocket_service.configure(
            FrameService(
                self._processor,
                resize=(settings.video.width, settings.video.height),
                capture_service=CaptureService(
                    capture_dir=settings.event.snapshot_dir,
                    enabled=settings.event.save_snapshots,
                ),
                event_publisher=self._event_publisher,
            )
        )

        if self._video_source is not None:
            self._stop_event.clear()
            self._video_thread = threading.Thread(
                target=self._processor.process_loop,
                args=(self._stop_event,),
                daemon=True,
                name="factoryguard-vision-ai",
            )
            self._video_thread.start()

        logger.info("Vision AI 파이프라인 시작 완료")

    def stop(self) -> None:
        self._stop_event.set()
        if self._video_thread and self._video_thread.is_alive():
            self._video_thread.join(timeout=5)
        if self._video_source is not None:
            self._video_source.release()
        if self._event_publisher is not None:
            self._event_publisher.stop()

        websocket_service.configure(None)
        self._video_thread = None
        self._video_source = None
        self._processor = None
        self._zone_manager = None
        self._event_publisher = None
        logger.info("Vision AI 리소스 반환 완료")

    def get_health(self) -> dict:
        return {
            "status": "healthy",
            "camera_id": settings.camera_id,
            "video_source": settings.video.source,
            "thread_active": (
                self._video_thread is not None and self._video_thread.is_alive()
            ),
            "websocket_pipeline_ready": websocket_service.frame_service is not None,
        }

    def get_zones(self) -> list[dict]:
        if self._zone_manager is None:
            return []

        return [
            {
                "zone_id": zone.zone_id,
                "name": zone.name,
                "points": zone.polygon.tolist(),
                "severity": zone.severity,
                "is_active": zone.is_active,
            }
            for zone in self._zone_manager.get_all_zones()
        ]

    def add_zone(self, zone_data: dict):
        if self._zone_manager is None:
            return None
        return self._zone_manager.add_zone(zone_data)


vision_ai_service = VisionAIService()
