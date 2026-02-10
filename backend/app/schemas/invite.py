from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.enums import InviteStatus, MembershipRole


class InviteCreate(BaseModel):
    invitee_id: Optional[int] = None
    invitee_email: Optional[EmailStr] = None
    membership_role: MembershipRole = MembershipRole.coauthor


class InviteAction(BaseModel):
    status: InviteStatus


class InviteOut(BaseModel):
    id: int
    project_id: int
    inviter_id: int
    invitee_id: int
    status: InviteStatus
    membership_role: MembershipRole
    invite_token: Optional[str]
    expires_at: Optional[datetime]
    accepted_at: Optional[datetime]
    rejected_at: Optional[datetime]
    revoked_at: Optional[datetime]
    revoked_by_id: Optional[int]
    created_at: datetime

    class Config:
        orm_mode = True
