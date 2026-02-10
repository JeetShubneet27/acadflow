from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import ReviewStatus


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    reviewer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    score = Column(Integer, nullable=True)
    comments = Column(Text, nullable=True)
    status = Column(Enum(ReviewStatus), nullable=False, default=ReviewStatus.pending)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="reviews")
    reviewer = relationship("User", back_populates="reviews")
