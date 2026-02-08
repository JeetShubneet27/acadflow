from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import PaymentStatus, PlagiarismStatus


class PlagiarismJobOut(BaseModel):
    id: int
    project_id: Optional[int]
    submitted_by_id: Optional[int]
    requester_email: Optional[str]
    requester_name: Optional[str]
    status: PlagiarismStatus
    eta_hours: int
    original_filename: str
    report_filename: Optional[str]
    payment_status: PaymentStatus
    amount_cents: int
    currency: str
    is_public: bool
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        orm_mode = True


class PublicPlagiarismJobOut(BaseModel):
    id: int
    access_token: str
    status: PlagiarismStatus
    eta_hours: int
    amount_cents: int
    currency: str


class PublicPlagiarismStatusOut(BaseModel):
    id: int
    status: PlagiarismStatus
    eta_hours: int
    amount_cents: int
    currency: str
    payment_status: PaymentStatus
    report_filename: Optional[str]
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        orm_mode = True


class PaymentUpdate(BaseModel):
    status: PaymentStatus
