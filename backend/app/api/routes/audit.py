from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.audit_event import AuditEvent
from app.models.enums import MemberStatus
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.audit import ActivityEventOut, AuditEventOut


router = APIRouter(tags=["audit"])


def _ensure_access(db: Session, project: Project, user: User) -> None:
    if user.role.value == "faculty":
        return
    is_member = (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project.id,
            ProjectMember.user_id == user.id,
            ProjectMember.status == MemberStatus.active,
        )
        .first()
        is not None
    )
    if project.owner_id != user.id and not is_member:
        raise HTTPException(status_code=403, detail="Not authorized")


def _ensure_owner_or_faculty(project: Project, user: User) -> None:
    if user.role.value == "faculty":
        return
    if project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")


def _summary_for_event(event: AuditEvent) -> str:
    metadata = event.event_metadata or {}
    if event.event_type == "project_created":
        return "Project created"
    if event.event_type == "project_visibility_changed":
        return f"Visibility updated to {metadata.get('visibility')}"
    if event.event_type == "invite_sent":
        return f"Invite sent to user {metadata.get('invitee_id')}"
    if event.event_type == "invite_accepted":
        return "Invite accepted"
    if event.event_type == "invite_rejected":
        return "Invite rejected"
    if event.event_type == "invite_revoked":
        return "Invite revoked"
    if event.event_type == "member_role_changed":
        return f"Member role changed to {metadata.get('role')}"
    if event.event_type == "member_status_changed":
        return f"Member status changed to {metadata.get('status')}"
    if event.event_type == "member_removed":
        return "Member removed"
    if event.event_type == "draft_uploaded":
        return f"Draft v{metadata.get('version')} uploaded"
    if event.event_type == "draft_locked":
        return "Draft locked"
    if event.event_type == "draft_lock_released":
        return "Draft lock released"
    if event.event_type == "annotation_created":
        return "Annotation added"
    if event.event_type == "annotation_resolved":
        return "Annotation resolved"
    if event.event_type == "annotation_reopened":
        return "Annotation reopened"
    if event.event_type == "annotation_replied":
        return "Annotation reply added"
    return event.event_type.replace("_", " ").title()


@router.get("/projects/{project_id}/audit", response_model=list[AuditEventOut])
def list_audit_events(
    project_id: int,
    since: Optional[datetime] = None,
    limit: int = 200,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[AuditEvent]:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _ensure_owner_or_faculty(project, current_user)
    query = db.query(AuditEvent).filter(AuditEvent.project_id == project_id)
    if since:
        query = query.filter(AuditEvent.created_at >= since)
    return query.order_by(AuditEvent.created_at.desc()).limit(min(limit, 500)).all()


@router.get("/projects/{project_id}/activity", response_model=list[ActivityEventOut])
def list_activity_feed(
    project_id: int,
    since: Optional[datetime] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ActivityEventOut]:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    _ensure_access(db, project, current_user)
    query = db.query(AuditEvent).filter(AuditEvent.project_id == project_id)
    if since:
        query = query.filter(AuditEvent.created_at >= since)
    events = query.order_by(AuditEvent.created_at.desc()).limit(min(limit, 200)).all()
    return [
        ActivityEventOut(
            id=event.id,
            actor_id=event.actor_id,
            event_type=event.event_type,
            summary=_summary_for_event(event),
            event_metadata=event.event_metadata,
            created_at=event.created_at,
        )
        for event in events
    ]
