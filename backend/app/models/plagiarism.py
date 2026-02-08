from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import PaymentStatus, PlagiarismStatus


class PlagiarismJob(Base):
    __tablename__ = "plagiarism_jobs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    draft_id = Column(Integer, ForeignKey("drafts.id"), nullable=True)
    submitted_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    requester_email = Column(String, nullable=True)
    requester_name = Column(String, nullable=True)
    public_access_token = Column(String, nullable=True, unique=True)
    status = Column(Enum(PlagiarismStatus), nullable=False, default=PlagiarismStatus.queued)
    eta_hours = Column(Integer, nullable=False, default=6)
    file_path = Column(String, nullable=False)
    original_filename = Column(String, nullable=False)
    payment_status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.pending)
    payment_method = Column(String, nullable=True)
    payment_provider = Column(String, nullable=True)
    payment_order_id = Column(String, nullable=True)
    payment_payment_id = Column(String, nullable=True)
    payment_signature = Column(String, nullable=True)
    payment_reference = Column(String, nullable=True)
    payment_submitted_at = Column(DateTime, nullable=True)
    amount_cents = Column(Integer, nullable=False, default=0)
    currency = Column(String, nullable=False, default="USD")
    is_public = Column(Boolean, nullable=False, default=False)
    report_file_path = Column(String, nullable=True)
    report_filename = Column(String, nullable=True)
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    project = relationship("Project", back_populates="plagiarism_jobs")
    submitted_by = relationship("User", back_populates="plagiarism_jobs", foreign_keys=[submitted_by_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])
