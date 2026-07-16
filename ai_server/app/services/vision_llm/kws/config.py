from __future__ import annotations

from dataclasses import dataclass, field

from app.config import settings as app_settings


@dataclass(frozen=True)
class KeywordSpec:
    keyword: str
    language: str
    aliases: tuple[str, ...] = ()
    risk_type: str = "비상정지"


DEFAULT_KEYWORDS: tuple[KeywordSpec, ...] = (
    KeywordSpec("멈춰", "ko", ("멈처", "멈춰줘", "멈추세요")),
    KeywordSpec("정지", "ko", ("중지", "스톱", "스탑")),
    KeywordSpec("살려줘", "ko", ("도와줘", "위험해")),
    KeywordSpec("stop", "en", ("emergency stop", "help")),
    KeywordSpec("dung lai", "vi", ("dừng lại", "cuu toi", "cứu tôi")),
    KeywordSpec("ting", "zh", ("停", "救命")),
)


@dataclass(frozen=True)
class KwsRuntimeSettings:
    threshold: float
    cooldown_seconds: float
    default_equipment: str
    default_location: str
    actuator_mode: str
    keywords: tuple[KeywordSpec, ...] = field(default_factory=lambda: DEFAULT_KEYWORDS)


def get_settings() -> KwsRuntimeSettings:
    config = app_settings.kws
    return KwsRuntimeSettings(
        threshold=config.threshold,
        cooldown_seconds=config.cooldown_seconds,
        default_equipment=config.default_equipment,
        default_location=config.default_location,
        actuator_mode=config.actuator_mode,
    )
