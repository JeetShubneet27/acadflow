from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import DraftLockStatus


class DraftLockOut(BaseModel):
    id: int
    draft_id: int
    locked_by_id: int
    status: DraftLockStatus
    locked_at: datetime
    expires_at: datetime
    released_at: Optional[datetime]

    class Config:
        orm_mode = True
