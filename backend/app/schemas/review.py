from datetime import datetime
from typing import Optional

from pydantic import BaseModel, conint

from app.models.enums import ReviewStatus


class ReviewAssign(BaseModel):
    reviewer_id: int


class ReviewSubmit(BaseModel):
    score: conint(ge=1, le=5)
    comments: Optional[str] = None


class ReviewOut(BaseModel):
    id: int
    project_id: int
    reviewer_id: int
    score: Optional[int]
    comments: Optional[str]
    status: ReviewStatus
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True
