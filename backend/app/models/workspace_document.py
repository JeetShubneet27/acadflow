from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import WorkspaceFormat


class WorkspaceDocument(Base):
    __tablename__ = "workspace_documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    title = Column(String, nullable=False)
    format = Column(Enum(WorkspaceFormat), nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    project = relationship("Project", back_populates="workspace_documents")
    created_by = relationship("User")
    revisions = relationship("WorkspaceRevision", back_populates="document", order_by="WorkspaceRevision.version")
    locks = relationship("WorkspaceLock", back_populates="document")
