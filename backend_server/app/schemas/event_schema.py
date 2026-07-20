from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class DetectionEventCreate(BaseModel):
    """Vision AI, DB, Frontend가 공유하는 위험 이벤트 계약."""

    event_id: str
    camera_id: str
    timestamp: datetime
    event_type: str
    severity: str
    status: str
    worker_id: int
    zone_name: str
    message: str
    snapshot_url: Optional[str] = None


class DetectionEventUpdate(BaseModel):
    status: str
    response_memo: Optional[str] = None
