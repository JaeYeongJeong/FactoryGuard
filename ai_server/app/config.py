"""
전체 설정 관리 모듈
환경변수 또는 .env 파일로 오버라이드 가능
"""

from pathlib import Path
from typing import Optional

from pydantic import AliasChoices, Field
from pydantic_settings import BaseSettings


PROJECT_ROOT = Path(__file__).resolve().parents[2]
AI_SERVER_ROOT = Path(__file__).resolve().parents[1]
ENV_FILES = (
    PROJECT_ROOT / ".env",
    AI_SERVER_ROOT / ".env",
    AI_SERVER_ROOT / "app" / ".env",
)


class DetectorSettings(BaseSettings):
    """YOLO26 감지 설정"""
    model_path: str = Field(default="yolo26n.pt", description="YOLO26 모델 경로")
    confidence_threshold: float = Field(default=0.5, description="감지 신뢰도 임계값")
    iou_threshold: float = Field(default=0.45, description="NMS IoU 임계값")
    device: str = Field(default="auto", description="추론 디바이스 (auto/cpu/cuda/0)")
    img_size: int = Field(default=640, description="추론 이미지 크기")
    target_classes: list[int] = Field(default=[0], description="감지 대상 클래스 ID (0=person)")

    class Config:
        env_prefix = "DETECTOR_"
        env_file = ENV_FILES
        env_file_encoding = "utf-8"
        extra = "ignore"


class TrackerSettings(BaseSettings):
    """ByteTrack 추적 설정"""
    track_thresh: float = Field(default=0.25, description="추적 신뢰도 임계값")
    track_buffer: int = Field(default=30, description="추적 버퍼 프레임 수")
    match_thresh: float = Field(default=0.8, description="매칭 임계값")

    class Config:
        env_prefix = "TRACKER_"
        env_file = ENV_FILES
        env_file_encoding = "utf-8"
        extra = "ignore"


class VideoSettings(BaseSettings):
    """영상 소스 설정"""
    source: str = Field(
        default="websocket://cam-01",
        description="영상 소스 경로 (websocket://카메라ID / 웹캠 인덱스 / RTSP URL / 파일)",
    )
    width: int = Field(default=1280, description="프레임 리사이즈 너비")
    height: int = Field(default=720, description="프레임 리사이즈 높이")
    fps_limit: int = Field(default=30, description="최대 FPS 제한")
    loop: bool = Field(default=True, description="영상 파일 반복 재생")

    class Config:
        env_prefix = "VIDEO_"
        env_file = ENV_FILES
        env_file_encoding = "utf-8"
        extra = "ignore"


class ZoneSettings(BaseSettings):
    """위험구역 설정"""
    poll_interval: int = Field(default=30, description="위험구역 폴링 간격 (초)")
    default_zones: list[dict] = Field(
        default=[],
        description="기본 위험구역 (API 연결 불가 시 사용)"
    )

    class Config:
        env_prefix = "ZONE_"
        env_file = ENV_FILES
        env_file_encoding = "utf-8"
        extra = "ignore"


class EventSettings(BaseSettings):
    """이벤트 전송 및 감도 튜닝 설정"""
    cooldown_seconds: float = Field(default=10.0, description="같은 이벤트 재전송 쿨다운 (초)")
    save_snapshots: bool = Field(default=True, description="최초 위험 감지 프레임 저장")
    snapshot_dir: str = Field(default="captures", description="위험 감지 프레임 저장 경로")
    
    # 감도 튜닝용 변수 복원
    intrusion_method: str = Field(default="pose-hybrid", description="침입 감지 방법 (point/multi-point/overlap/segment/pose-hybrid)")
    overlap_ratio: float = Field(default=0.2, description="overlap 방식 사용 시 바운딩박스 하부 비율")
    pose_conf_threshold: float = Field(default=0.5, description="포즈 키포인트 검출 신뢰도 임계치")
    waving_amplitude_ratio: float = Field(default=0.15, description="손 흔들기 최소 진폭 비율 (어깨 너비 대비)")
    waving_direction_changes: int = Field(default=2, description="손 흔들기 최소 방향 전환 횟수")
    waving_min_frames: int = Field(default=8, description="손 흔들기 판단을 위해 최소로 필요한 누적 프레임 수")
    waving_conf_threshold: float = Field(default=0.25, description="손 흔들기 전용 관절 검출 신뢰도 임계값 (낮을수록 민감)")
    waving_y_ratio: float = Field(default=0.6, description="어깨 기준 손 높이 허용 범위 비율 (클수록 낮은 위치도 허용)")
    waving_history_frames: int = Field(default=30, description="손 흔들기 궤적 최대 보관 프레임 수")
    waving_smooth_window: int = Field(default=3, description="이동 평균 스무딩 윈도우 크기 (클수록 떨림에 둔감)")
    waving_pixel_threshold: float = Field(default=5.0, description="방향 전환 감지 최소 이동 픽셀 (클수록 큰 움직임만 감지)")
    waving_speed_threshold: float = Field(default=8.0, description="손 흔들기 최소 속도 임계치 (픽셀/프레임)")
    enter_threshold_frames: int = Field(default=3, description="위험 감지 판정에 필요한 최소 연속 프레임 수")
    exit_threshold_frames: int = Field(default=5, description="위험 해제 판정에 필요한 최소 연속 프레임 수")

    class Config:
        env_prefix = "EVENT_"
        env_file = ENV_FILES
        env_file_encoding = "utf-8"
        extra = "ignore"


class APISettings(BaseSettings):
    """백엔드 API 설정"""
    backend_url: str = Field(default="http://localhost:8000", description="백엔드 API 베이스 URL")
    backend_public_url: Optional[str] = Field(
        default=None,
        description="프론트에서 접근 가능한 백엔드 URL",
    )
    ai_url: str = Field(
        default="http://localhost:8001",
        description="서비스 내부에서 접근하는 AI 서버 URL",
    )
    ai_public_url: str = Field(
        default="http://localhost:8001",
        description="프론트에서 접근 가능한 AI 서버 URL",
    )
    capture_base_url: Optional[str] = Field(
        default=None,
        description="파일명을 제외한 공개 캡처 URL (예: https://ai.example.com/captures)",
    )
    ws_url: str = Field(default="ws://localhost:8000/events/stream", description="WebSocket URL")
    openai_api_key: Optional[str] = Field(
        default=None,
        validation_alias=AliasChoices("OPENAI_API_KEY", "API_OPENAI_API_KEY"),
        description="OpenAI API 인증 키",
    )
    timeout: float = Field(default=5.0, description="API 요청 타임아웃 (초)")
    retry_count: int = Field(default=3, description="API 요청 재시도 횟수")

    class Config:
        env_prefix = "API_"
        env_file = ENV_FILES
        env_file_encoding = "utf-8"
        extra = "ignore"


class AppSettings(BaseSettings):
    """전체 앱 설정"""
    camera_id: str = Field(default="cam-01", description="카메라 식별자")
    show_display: bool = Field(default=True, description="시각화 디스플레이 표시")
    log_level: str = Field(default="INFO", description="로그 레벨")

    detector: DetectorSettings = Field(default_factory=DetectorSettings)
    tracker: TrackerSettings = Field(default_factory=TrackerSettings)
    video: VideoSettings = Field(default_factory=VideoSettings)
    zone: ZoneSettings = Field(default_factory=ZoneSettings)
    event: EventSettings = Field(default_factory=EventSettings)
    api: APISettings = Field(default_factory=APISettings)

    class Config:
        env_prefix = "APP_"
        env_file = ENV_FILES
        env_file_encoding = "utf-8"
        extra = "ignore"


# 전역 설정 인스턴스
settings = AppSettings()
