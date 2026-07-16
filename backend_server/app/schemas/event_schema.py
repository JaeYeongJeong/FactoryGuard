from datetime import datetime

from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class DetectionEventCreate(BaseModel):
    event_id: str
    camera_id: str
    event_type: str
    severity: str
    confidence: float = Field(
        ge=0,
        le=1,
    )
    track_id: int | None = None
    bbox: BoundingBox
    detected_at: datetime
    message: str