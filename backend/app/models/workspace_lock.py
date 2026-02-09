from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import DraftLockStatus


class WorkspaceLock(Base):
    __tablename__ = "workspace_locks"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("workspace_documents.id"), nullable=False)
    locked_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(DraftLockStatus), nullable=False, default=DraftLockStatus.active)
    locked_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    released_at = Column(DateTime, nullable=True)

    document = relationship("WorkspaceDocument", back_populates="locks")
    locked_by = relationship("User")
