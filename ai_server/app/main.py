import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.responses import JSONResponse
from loguru import logger

from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from app.routers.ws_router import router as ws_router
from app.routers.reports_router import router as reports_router

from app.config import settings
from app.services import (
    DangerZoneManager,
    create_video_source,
    FrameProcessor,
    IntrusionDetector,
    PersonDetector,
    PersonTracker,
    FrameRenderer,
)

# 백그라운드 제어용 전역 변수
video_thread = None
stop_event = threading.Event()
processor_instance = None
zone_manager_instance = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI 구동 수명 주기: 비전 프로세싱 백그라운드 루프 구동 및 정지 관리"""
    global video_thread, stop_event, processor_instance, zone_manager_instance
    logger.info("⚡ [FactoryGuard AI Server] 비전 안전 분석 백그라운드 스레드 시동 중...")

    # 1. 비전 서비스 인스턴스 조립
    zone_manager_instance = DangerZoneManager(
        camera_id=settings.camera_id,
        poll_interval=settings.zone.poll_interval,
        default_zones=settings.zone.default_zones
    )
    
    # 임시 데모 구역 자동 설정
    zone_manager_instance.set_demo_zones(settings.video.width, settings.video.height)

    detector = PersonDetector(
        model_path=settings.detector.model_path,
        confidence_threshold=settings.detector.confidence_threshold,
        iou_threshold=settings.detector.iou_threshold,
        device=settings.detector.device,
        img_size=settings.detector.img_size,
        target_classes=settings.detector.target_classes
    )

    tracker = PersonTracker(
        track_thresh=settings.tracker.track_thresh,
        track_buffer=settings.tracker.track_buffer,
        match_thresh=settings.tracker.match_thresh
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
        exit_threshold_frames=settings.event.exit_threshold_frames
    )

    renderer = FrameRenderer()
    video_source = create_video_source(settings.video.source)

    if not video_source.open():
        logger.error("❌ 비디오 소스 열기 실패. 백그라운드 분석을 건너뜁니다.")
        yield
        return

    # 오케스트레이터 생성
    processor_instance = FrameProcessor(
        video_source=video_source,
        detector=detector,
        tracker=tracker,
        intrusion_detector=intrusion_detector,
        renderer=renderer,
        zone_manager=zone_manager_instance,
        event_sender=None,
        show_display=settings.show_display
    )

    # 2. 백그라운드 실행용 스레드 스핀업
    stop_event.clear()
    video_thread = threading.Thread(
        target=processor_instance.process_loop,
        args=(stop_event,),
        daemon=True
    )
    video_thread.start()
    logger.info("🟢 [FactoryGuard AI Server] 비전 스레드가 성공적으로 시작되었습니다.")

    yield  # 애플리케이션 서비스 진행 영역

    # 3. 종료 시 리소스 반환
    logger.info("🔴 [FactoryGuard AI Server] 비전 스레드 정지 중...")
    stop_event.set()
    if video_thread and video_thread.is_alive():
        video_thread.join(timeout=5)
    video_source.release()
    logger.info("⚡ [FactoryGuard AI Server] 비전 리소스 반환 및 안전 종료 완료")


# FastAPI 기동
app = FastAPI(
    title="FactoryGuard AI Server",
    description="실시간 위험구역 침입 및 이상 자세 감지 분석 엔진 API",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 데모용. 운영에서는 프론트 도메인만 허용하세요.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ws_router)
app.include_router(reports_router)


@app.get("/health")
async def health_check():
    """AI 분석 서버 헬스 체크 API"""
    return {
        "status": "healthy",
        "camera_id": settings.camera_id,
        "video_source": settings.video.source,
        "thread_active": video_thread is not None and video_thread.is_alive()
    }


@app.get("/api/zones")
async def get_current_zones():
    """현재 작동 중인 위험구역 목록 반환"""
    if not zone_manager_instance:
        return {"zones": []}
    
    zones = zone_manager_instance.get_all_zones()
    return {
        "zones": [
            {
                "zone_id": z.zone_id,
                "name": z.name,
                "points": z.polygon.tolist() if hasattr(z.polygon, "tolist") else list(z.polygon),
                "severity": z.severity,
                "is_active": z.is_active
            }
            for z in zones
        ]
    }


@app.post("/api/zones")
async def add_custom_zone(zone_data: dict):
    """실시간 API로 위험구역 신규 등록"""
    if not zone_manager_instance:
        return JSONResponse(status_code=503, content={"error": "서버 초기화 미완료"})
    
    # 수동 좌표 형식: {"zone_id": "zone_1", "name": "A구역", "points": [[x1,y1], ...], "severity": "high"}
    added_zone = zone_manager_instance.add_zone(zone_data)
    if added_zone:
        return {"success": True, "added_zone_id": added_zone.zone_id}
    return JSONResponse(status_code=400, content={"error": "구역 파싱 실패. 최소 3개 이상 points 필요"})
