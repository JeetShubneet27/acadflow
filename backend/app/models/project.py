from datetime import datetime

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.db.base import Base
from app.models.enums import ProjectVisibility


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    abstract = Column(Text, nullable=True)
    visibility = Column(Enum(ProjectVisibility), nullable=False, default=ProjectVisibility.private)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    owner = relationship("User", back_populates="owned_projects")
    members = relationship("ProjectMember", back_populates="project")
    invites = relationship("ProjectInvite", back_populates="project")
    drafts = relationship("Draft", back_populates="project")
    workspace_documents = relationship("WorkspaceDocument", back_populates="project")
    reviews = relationship("Review", back_populates="project")
    plagiarism_jobs = relationship("PlagiarismJob", back_populates="project")
