from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from app.models.enums import DraftLockStatus, WorkspaceFormat


class WorkspaceDocumentCreate(BaseModel):
    title: str
    content: Optional[str] = None


class WorkspaceDocumentOut(BaseModel):
    id: int
    project_id: int
    title: str
    format: WorkspaceFormat
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    latest_version: Optional[int]
    latest_updated_at: Optional[datetime]

    class Config:
        orm_mode = True


class WorkspaceRevisionOut(BaseModel):
    id: int
    document_id: int
    version: int
    created_by_id: int
    created_at: datetime
    original_filename: Optional[str]
    content_text: Optional[str]

    class Config:
        orm_mode = True


class WorkspaceLatexUpdate(BaseModel):
    content: str


class WorkspaceLockOut(BaseModel):
    id: int
    document_id: int
    locked_by_id: int
    status: DraftLockStatus
    locked_at: datetime
    expires_at: datetime
    released_at: Optional[datetime]

    class Config:
        orm_mode = True
