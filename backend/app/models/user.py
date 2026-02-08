from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, Integer, String
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import RoleEnum


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.student)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    owned_projects = relationship("Project", back_populates="owner")
    memberships = relationship("ProjectMember", back_populates="user")
    invites_received = relationship(
        "ProjectInvite",
        back_populates="invitee",
        foreign_keys="ProjectInvite.invitee_id",
    )
    invites_sent = relationship(
        "ProjectInvite",
        back_populates="inviter",
        foreign_keys="ProjectInvite.inviter_id",
    )
    reviews = relationship("Review", back_populates="reviewer")
    plagiarism_jobs = relationship("PlagiarismJob", back_populates="submitted_by")
