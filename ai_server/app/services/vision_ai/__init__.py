"""Vision AI 서비스 공개 API를 지연 로딩합니다."""

from importlib import import_module


_EXPORTS = {
    "PersonDetector": ("app.services.vision_ai.core.detector", "PersonDetector"),
    "MediaPipeDetector": (
        "app.services.vision_ai.core.mediapipe_detector",
        "MediaPipeDetector",
    ),
    "PersonTracker": ("app.services.vision_ai.core.tracker", "PersonTracker"),
    "TrackedObject": ("app.services.vision_ai.core.tracker", "TrackedObject"),
    "DangerZoneManager": (
        "app.services.vision_ai.core.zone_manager",
        "DangerZoneManager",
    ),
    "DangerZone": ("app.services.vision_ai.core.zone_manager", "DangerZone"),
    "IntrusionDetector": (
        "app.services.vision_ai.processing.intrusion_detector",
        "IntrusionDetector",
    ),
    "IntrusionEvent": (
        "app.services.vision_ai.processing.intrusion_detector",
        "IntrusionEvent",
    ),
    "IntrusionState": (
        "app.services.vision_ai.processing.intrusion_detector",
        "IntrusionState",
    ),
    "_TrackerZoneState": (
        "app.services.vision_ai.processing.intrusion_detector",
        "_TrackerZoneState",
    ),
    "FrameProcessor": (
        "app.services.vision_ai.processing.frame_processor",
        "FrameProcessor",
    ),
    "FrameService": ("app.services.vision_ai.frame_service", "FrameService"),
    "CaptureService": ("app.services.vision_ai.capture_service", "CaptureService"),
    "create_video_source": (
        "app.services.vision_ai.processing.video_source",
        "create_video_source",
    ),
    "FrameRenderer": (
        "app.services.vision_ai.visualization.renderer",
        "FrameRenderer",
    ),
    "ZoneDrawer": ("app.services.vision_ai.visualization.drawer", "ZoneDrawer"),
    "is_point_in_polygon": (
        "app.services.vision_ai.utils.geometry",
        "is_point_in_polygon",
    ),
    "polygon_from_points": (
        "app.services.vision_ai.utils.geometry",
        "polygon_from_points",
    ),
    "get_bottom_center": (
        "app.services.vision_ai.utils.geometry",
        "get_bottom_center",
    ),
    "calculate_iou": ("app.services.vision_ai.utils.geometry", "calculate_iou"),
    "get_multi_bottom_points": (
        "app.services.vision_ai.utils.geometry",
        "get_multi_bottom_points",
    ),
    "check_polygon_overlap_mask": (
        "app.services.vision_ai.utils.geometry",
        "check_polygon_overlap_mask",
    ),
    "check_segment_overlap_mask": (
        "app.services.vision_ai.utils.geometry",
        "check_segment_overlap_mask",
    ),
}

__all__ = list(_EXPORTS)


def __getattr__(name: str):
    try:
        module_name, attribute_name = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    value = getattr(import_module(module_name), attribute_name)
    globals()[name] = value
    return value
