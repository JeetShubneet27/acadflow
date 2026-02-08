from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import ProjectVisibility, MembershipRole


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
    created_at: datetime

    class Config:
        orm_mode = True
