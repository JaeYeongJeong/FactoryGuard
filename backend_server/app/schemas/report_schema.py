from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class IncidentReportCreate(BaseModel):
    report_id: str
    event_id: str | None = None
    source: str
    created_at: datetime
    report: str
    legal_basis: list[dict[str, Any]] = Field(default_factory=list)
    recommended_action: list[str] = Field(default_factory=list)
    rag_available: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)


class IncidentReportAnalysisRequest(BaseModel):
    use_rag: bool = True
