"""서비스 공개 API를 무거운 AI 의존성 없이 지연 로딩합니다."""

from importlib import import_module


_EXPORTS = {
    "PersonDetector": ("app.services.core.detector", "PersonDetector"),
    "MediaPipeDetector": ("app.services.core.mediapipe_detector", "MediaPipeDetector"),
    "PersonTracker": ("app.services.core.tracker", "PersonTracker"),
    "TrackedObject": ("app.services.core.tracker", "TrackedObject"),
    "DangerZoneManager": ("app.services.core.zone_manager", "DangerZoneManager"),
    "DangerZone": ("app.services.core.zone_manager", "DangerZone"),
    "IntrusionDetector": ("app.services.processing.intrusion_detector", "IntrusionDetector"),
    "IntrusionEvent": ("app.services.processing.intrusion_detector", "IntrusionEvent"),
    "IntrusionState": ("app.services.processing.intrusion_detector", "IntrusionState"),
    "_TrackerZoneState": ("app.services.processing.intrusion_detector", "_TrackerZoneState"),
    "FrameProcessor": ("app.services.processing.frame_processor", "FrameProcessor"),
    "FrameService": ("app.services.frame_service", "FrameService"),
    "create_video_source": ("app.services.processing.video_source", "create_video_source"),
    "FrameRenderer": ("app.services.visualization.renderer", "FrameRenderer"),
    "ZoneDrawer": ("app.services.visualization.drawer", "ZoneDrawer"),
    "is_point_in_polygon": ("app.services.utils.geometry", "is_point_in_polygon"),
    "polygon_from_points": ("app.services.utils.geometry", "polygon_from_points"),
    "get_bottom_center": ("app.services.utils.geometry", "get_bottom_center"),
    "calculate_iou": ("app.services.utils.geometry", "calculate_iou"),
    "get_multi_bottom_points": ("app.services.utils.geometry", "get_multi_bottom_points"),
    "check_polygon_overlap_mask": ("app.services.utils.geometry", "check_polygon_overlap_mask"),
    "check_segment_overlap_mask": ("app.services.utils.geometry", "check_segment_overlap_mask"),
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
