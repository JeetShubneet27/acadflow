from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel

from app.models.enums import AnnotationStatus


class AnnotationCreate(BaseModel):
    anchor_type: str
    anchor_data: Optional[dict[str, Any]] = None
    body: str
    parent_id: Optional[int] = None


class AnnotationUpdate(BaseModel):
    body: str


class AnnotationOut(BaseModel):
    id: int
    draft_id: int
    author_id: int
    parent_id: Optional[int]
    anchor_type: str
    anchor_data: Optional[dict[str, Any]]
    body: str
    status: AnnotationStatus
    created_at: datetime
    updated_at: Optional[datetime]
    resolved_at: Optional[datetime]
    resolved_by_id: Optional[int]

    class Config:
        orm_mode = True
