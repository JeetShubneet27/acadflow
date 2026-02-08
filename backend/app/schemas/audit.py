from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class AuditEventOut(BaseModel):
    id: int
    project_id: Optional[int]
    actor_id: Optional[int]
    event_type: str
    entity_type: Optional[str]
    entity_id: Optional[int]
    metadata: Optional[dict[str, Any]]
    created_at: datetime

    class Config:
        orm_mode = True


class ActivityEventOut(BaseModel):
    id: int
    actor_id: Optional[int]
    event_type: str
    summary: str
    metadata: Optional[dict[str, Any]]
    created_at: datetime

    class Config:
        orm_mode = True
