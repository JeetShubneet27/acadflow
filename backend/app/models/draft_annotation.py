from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, JSON, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import AnnotationStatus


class DraftAnnotation(Base):
    __tablename__ = "draft_annotations"

    id = Column(Integer, primary_key=True, index=True)
    draft_id = Column(Integer, ForeignKey("drafts.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_id = Column(Integer, ForeignKey("draft_annotations.id"), nullable=True)
    anchor_type = Column(Text, nullable=False)
    anchor_data = Column(JSON, nullable=True)
    body = Column(Text, nullable=False)
    status = Column(Enum(AnnotationStatus), nullable=False, default=AnnotationStatus.open)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    draft = relationship("Draft")
    author = relationship("User", foreign_keys=[author_id])
    resolved_by = relationship("User", foreign_keys=[resolved_by_id])
    parent = relationship("DraftAnnotation", remote_side=[id])
