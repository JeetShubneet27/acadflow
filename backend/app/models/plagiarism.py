from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import PlagiarismStatus


class PlagiarismJob(Base):
    __tablename__ = "plagiarism_jobs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    draft_id = Column(Integer, ForeignKey("drafts.id"), nullable=True)
    submitted_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(PlagiarismStatus), nullable=False, default=PlagiarismStatus.queued)
    eta_hours = Column(Integer, nullable=False, default=6)
    file_path = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    report_file_path = Column(String, nullable=True)
    report_filename = Column(String, nullable=True)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="plagiarism_jobs")
    submitted_by = relationship("User", back_populates="plagiarism_jobs", foreign_keys=[submitted_by_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
