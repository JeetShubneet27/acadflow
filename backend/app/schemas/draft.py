from datetime import datetime

from pydantic import BaseModel


class DraftOut(BaseModel):
    id: int
    project_id: int
    version: int
    original_filename: str
    created_at: datetime

    class Config:
        orm_mode = True
