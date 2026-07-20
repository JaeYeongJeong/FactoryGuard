from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DetectionEventCreate(BaseModel):
    """Vision AI, DB, Frontend가 공유하는 위험 이벤트 계약."""

    event_id: str
    camera_id: str
    timestamp: datetime
    last_seen_at: Optional[datetime] = None
    exited_at: Optional[datetime] = None
    duration: float = 0.0
    event_type: str
    severity: str
    status: str
    response_status: Optional[str] = None
    worker_id: int
    zone_name: str
    message: str
    snapshot_url: Optional[str] = None


class DetectionEventUpdate(BaseModel):
    response_status: str
    response_memo: Optional[str] = None
