from datetime import datetime

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base


class WorkspaceRevision(Base):
    __tablename__ = "workspace_revisions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("workspace_documents.id"), nullable=False)
    version = Column(Integer, nullable=False)
    content_text = Column(Text, nullable=True)
    file_path = Column(String, nullable=True)
    original_filename = Column(String, nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    document = relationship("WorkspaceDocument", back_populates="revisions")
    created_by = relationship("User")
