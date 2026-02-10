from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl


class ConferenceCreate(BaseModel):
    title: str
    website: Optional[HttpUrl] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    submission_deadline: Optional[date] = None
    description: Optional[str] = None


class ConferenceOut(BaseModel):
    id: int
    title: str
    website: Optional[str] = None
    location: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    submission_deadline: Optional[date] = None
    description: Optional[str] = None
    created_by_id: int
    created_at: datetime

    class Config:
        orm_mode = True
