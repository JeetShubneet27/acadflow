from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import InviteStatus, MembershipRole


class ProjectInvite(Base):
    __tablename__ = "project_invites"
    __table_args__ = (UniqueConstraint("project_id", "invitee_id", name="uq_project_invite"),)

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    inviter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    invitee_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(InviteStatus), nullable=False, default=InviteStatus.pending)
    membership_role = Column(Enum(MembershipRole), nullable=False, default=MembershipRole.coauthor)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    project = relationship("Project", back_populates="invites")
    inviter = relationship("User", back_populates="invites_sent", foreign_keys=[inviter_id])
    invitee = relationship("User", back_populates="invites_received", foreign_keys=[invitee_id])
