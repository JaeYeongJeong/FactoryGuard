from typing import Any, Literal

from pydantic import BaseModel, Field


RouteName = Literal["safety", "privacy"]
SourceName = Literal["vision", "kws", "backend", "manual", "unknown"]


class RagEventPayload(BaseModel):
    event_id: str | None = None
    source: SourceName = "unknown"
    timestamp: str | None = None
    risk_type: str | None = None
    object: str | None = None
    equipment: str | None = None
    location: str | None = None
    description: str | None = None
    observed_action: str | None = None
    hazard_tags: list[str] = Field(default_factory=list)
    kws_keywords: list[str] = Field(default_factory=list)
    vision_labels: list[str] = Field(default_factory=list)
    extra: dict[str, Any] = Field(default_factory=dict)


class RagSearchRequest(BaseModel):
    event: RagEventPayload
    route: RouteName | None = None
    top_k: int = Field(default=5, ge=1, le=20)
    candidate_multiplier: int = Field(default=8, ge=3, le=20)


class RagReportRequest(RagSearchRequest):
    include_markdown: bool = True


class KwsSimulateRequest(BaseModel):
    text: str = Field(min_length=1)
    location: str | None = None
    equipment: str | None = None
    line_id: str | None = None
    force_stop: bool = True


class KwsStopTestRequest(BaseModel):
    reason: str = "manual_stop_test"
    location: str | None = None
    equipment: str | None = None
