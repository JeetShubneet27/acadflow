from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import PlagiarismStatus


class PlagiarismJobOut(BaseModel):
    id: int
    project_id: int
    submitted_by_id: int
    status: PlagiarismStatus
    eta_hours: int
    original_filename: str
    report_filename: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        orm_mode = True
