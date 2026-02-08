from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import MemberStatus, MembershipRole, ProjectVisibility


class ProjectCreate(BaseModel):
    title: str
    abstract: Optional[str] = None
    visibility: ProjectVisibility = ProjectVisibility.private


class ProjectOut(BaseModel):
    id: int
    title: str
    abstract: Optional[str]
    visibility: ProjectVisibility
    owner_id: int
    created_at: datetime

    class Config:
        orm_mode = True


class ProjectVisibilityUpdate(BaseModel):
    visibility: ProjectVisibility


class ProjectMemberOut(BaseModel):
    user_id: int
    role: MembershipRole
    status: MemberStatus
    created_at: datetime

    class Config:
        orm_mode = True


class ProjectMemberRoleUpdate(BaseModel):
    role: MembershipRole


class ProjectMemberStatusUpdate(BaseModel):
    status: MemberStatus


class ProjectPermissionsOut(BaseModel):
    can_view: bool
    can_invite: bool
    can_manage_members: bool
    can_change_visibility: bool
    can_upload_drafts: bool
    can_comment: bool
    can_assign_reviewers: bool
