from datetime import datetime, timedelta
from typing import Optional
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.core.config import settings
from app.models.enums import InviteStatus, MemberStatus, MembershipRole, ProjectVisibility
from app.models.project import Project
from app.models.project_invite import ProjectInvite
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.invite import InviteAction, InviteCreate, InviteOut
from app.schemas.project import (
    ProjectCreate,
    ProjectMemberOut,
    ProjectMemberRoleUpdate,
    ProjectMemberStatusUpdate,
    ProjectOut,
    ProjectPermissionsOut,
    ProjectVisibilityUpdate,
)
from app.utils.audit import log_event


router = APIRouter(tags=["projects"])


def _get_project(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def _is_project_member(db: Session, project_id: int, user_id: int) -> bool:
    return (
        db.query(ProjectMember)
        .filter(
            ProjectMember.project_id == project_id,
            ProjectMember.user_id == user_id,
            ProjectMember.status == MemberStatus.active,
        )
        .first()
        is not None
    )


def _expire_invite_if_needed(invite: ProjectInvite) -> bool:
    if invite.status == InviteStatus.pending and invite.expires_at:
        if invite.expires_at < datetime.utcnow():
            invite.status = InviteStatus.expired
            return True
    return False


def _project_permissions(
    project: Project, member: Optional[ProjectMember], user: User
) -> ProjectPermissionsOut:
    if user.role.value == "faculty":
        return ProjectPermissionsOut(
            can_view=True,
            can_invite=True,
            can_manage_members=True,
            can_change_visibility=True,
            can_upload_drafts=True,
            can_comment=True,
            can_assign_reviewers=True,
        )
    is_owner = project.owner_id == user.id
    is_active_member = member is not None and member.status == MemberStatus.active
    return ProjectPermissionsOut(
        can_view=is_owner or is_active_member,
        can_invite=is_owner,
        can_manage_members=is_owner,
        can_change_visibility=is_owner,
        can_upload_drafts=is_owner or is_active_member,
        can_comment=is_owner or is_active_member,
        can_assign_reviewers=False,
    )


@router.post("/projects", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project = Project(
        title=payload.title,
        abstract=payload.abstract,
        visibility=payload.visibility,
        owner_id=current_user.id,
    )
    db.add(project)
    db.flush()
    membership = ProjectMember(
        project_id=project.id,
        user_id=current_user.id,
        role=MembershipRole.owner,
    )
    db.add(membership)
    db.commit()
    db.refresh(project)
    log_event(
        db,
        project_id=project.id,
        actor_id=current_user.id,
        event_type="project_created",
        entity_type="project",
        entity_id=project.id,
        metadata={"title": project.title},
    )
    db.commit()
    return project


@router.get("/projects", response_model=list[ProjectOut])
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Project]:
    if current_user.role.value == "faculty":
        return db.query(Project).order_by(Project.created_at.desc()).all()
    projects = (
        db.query(Project)
        .outerjoin(ProjectMember, ProjectMember.project_id == Project.id)
        .filter(
            or_(
                Project.owner_id == current_user.id,
                ProjectMember.user_id == current_user.id,
            ),
            or_(ProjectMember.status == MemberStatus.active, ProjectMember.id.is_(None)),
        )
        .distinct()
        .order_by(Project.created_at.desc())
        .all()
    )
    return projects


@router.get("/projects/public", response_model=list[ProjectOut])
def list_public_projects(db: Session = Depends(get_db)) -> list[Project]:
    return (
        db.query(Project)
        .filter(Project.visibility == ProjectVisibility.public)
        .order_by(Project.created_at.desc())
        .all()
    )


@router.get("/projects/{project_id}", response_model=ProjectOut)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project = _get_project(db, project_id)
    if current_user.role.value == "faculty":
        return project
    if project.owner_id != current_user.id and not _is_project_member(db, project_id, current_user.id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return project


@router.put("/projects/{project_id}/visibility", response_model=ProjectOut)
def update_visibility(
    project_id: int,
    payload: ProjectVisibilityUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Project:
    project = _get_project(db, project_id)
    if current_user.role.value != "faculty" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    project.visibility = payload.visibility
    db.commit()
    db.refresh(project)
    log_event(
        db,
        project_id=project.id,
        actor_id=current_user.id,
        event_type="project_visibility_changed",
        entity_type="project",
        entity_id=project.id,
        metadata={"visibility": project.visibility.value},
    )
    db.commit()
    return project


@router.get("/projects/{project_id}/members", response_model=list[ProjectMemberOut])
def list_members(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectMember]:
    project = _get_project(db, project_id)
    if (
        current_user.role.value != "faculty"
        and project.owner_id != current_user.id
        and not _is_project_member(db, project_id, current_user.id)
    ):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return db.query(ProjectMember).filter(ProjectMember.project_id == project_id).all()


@router.get("/projects/{project_id}/permissions", response_model=ProjectPermissionsOut)
def get_permissions(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectPermissionsOut:
    project = _get_project(db, project_id)
    member = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == current_user.id)
        .first()
    )
    permissions = _project_permissions(project, member, current_user)
    if not permissions.can_view:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return permissions


@router.post("/projects/{project_id}/invite", response_model=InviteOut, status_code=status.HTTP_201_CREATED)
def invite_member(
    project_id: int,
    payload: InviteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectInvite:
    project = _get_project(db, project_id)
    if current_user.role.value != "faculty" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    invitee = None
    if payload.invitee_id is not None:
        invitee = db.get(User, payload.invitee_id)
    elif payload.invitee_email is not None:
        invitee = db.query(User).filter(User.email == payload.invitee_email).first()
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invitee required")

    if not invitee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invitee not found")

    if _is_project_member(db, project_id, invitee.id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User already a member")

    existing_invite = (
        db.query(ProjectInvite)
        .filter(
            ProjectInvite.project_id == project_id,
            ProjectInvite.invitee_id == invitee.id,
        )
        .first()
    )
    expires_at = datetime.utcnow() + timedelta(hours=settings.invite_expiry_hours)
    if existing_invite:
        if existing_invite.status == InviteStatus.pending:
            if existing_invite.expires_at and existing_invite.expires_at < datetime.utcnow():
                existing_invite.status = InviteStatus.expired
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite already pending")
        existing_invite.status = InviteStatus.pending
        existing_invite.membership_role = payload.membership_role
        existing_invite.invite_token = existing_invite.invite_token or uuid4().hex
        existing_invite.expires_at = expires_at
        existing_invite.revoked_at = None
        existing_invite.revoked_by_id = None
        db.commit()
        db.refresh(existing_invite)
        log_event(
            db,
            project_id=project_id,
            actor_id=current_user.id,
            event_type="invite_sent",
            entity_type="invite",
            entity_id=existing_invite.id,
            metadata={"invitee_id": invitee.id},
        )
        db.commit()
        return existing_invite

    invite = ProjectInvite(
        project_id=project_id,
        inviter_id=current_user.id,
        invitee_id=invitee.id,
        status=InviteStatus.pending,
        membership_role=payload.membership_role,
        invite_token=uuid4().hex,
        expires_at=expires_at,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    log_event(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        event_type="invite_sent",
        entity_type="invite",
        entity_id=invite.id,
        metadata={"invitee_id": invitee.id},
    )
    db.commit()
    return invite


@router.get("/projects/invites", response_model=list[InviteOut])
def list_invites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectInvite]:
    invites = (
        db.query(ProjectInvite)
        .filter(ProjectInvite.invitee_id == current_user.id)
        .order_by(ProjectInvite.created_at.desc())
        .all()
    )
    updated = False
    for invite in invites:
        if _expire_invite_if_needed(invite):
            updated = True
    if updated:
        db.commit()
    return invites


@router.get("/projects/{project_id}/invites", response_model=list[InviteOut])
def list_project_invites(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectInvite]:
    project = _get_project(db, project_id)
    if current_user.role.value != "faculty" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    invites = db.query(ProjectInvite).filter(ProjectInvite.project_id == project_id).all()
    updated = False
    for invite in invites:
        if _expire_invite_if_needed(invite):
            updated = True
    if updated:
        db.commit()
    return invites


@router.put("/projects/invites/{invite_id}", response_model=InviteOut)
def respond_invite(
    invite_id: int,
    payload: InviteAction,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectInvite:
    invite = db.get(ProjectInvite, invite_id)
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    if _expire_invite_if_needed(invite):
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite expired")
    if invite.status == InviteStatus.revoked:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite revoked")
    if invite.invitee_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if invite.status != InviteStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite already processed")

    if payload.status == InviteStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invite action")

    if payload.status == InviteStatus.accepted:
        member = ProjectMember(
            project_id=invite.project_id,
            user_id=current_user.id,
            role=invite.membership_role,
            status=MemberStatus.active,
        )
        db.add(member)
        invite.accepted_at = datetime.utcnow()
    invite.status = payload.status
    if payload.status == InviteStatus.rejected:
        invite.rejected_at = datetime.utcnow()
    db.commit()
    db.refresh(invite)
    log_event(
        db,
        project_id=invite.project_id,
        actor_id=current_user.id,
        event_type="invite_accepted" if payload.status == InviteStatus.accepted else "invite_rejected",
        entity_type="invite",
        entity_id=invite.id,
    )
    db.commit()
    return invite


@router.delete("/projects/invites/{invite_id}", response_model=InviteOut)
def revoke_invite(
    invite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectInvite:
    invite = db.get(ProjectInvite, invite_id)
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    project = _get_project(db, invite.project_id)
    if current_user.role.value != "faculty" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if invite.status != InviteStatus.pending:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite already processed")
    invite.status = InviteStatus.revoked
    invite.revoked_at = datetime.utcnow()
    invite.revoked_by_id = current_user.id
    db.commit()
    db.refresh(invite)
    log_event(
        db,
        project_id=invite.project_id,
        actor_id=current_user.id,
        event_type="invite_revoked",
        entity_type="invite",
        entity_id=invite.id,
    )
    db.commit()
    return invite


@router.post("/projects/invites/{invite_id}/resend", response_model=InviteOut)
def resend_invite(
    invite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectInvite:
    invite = db.get(ProjectInvite, invite_id)
    if not invite:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invite not found")
    project = _get_project(db, invite.project_id)
    if current_user.role.value != "faculty" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    if invite.status not in {InviteStatus.revoked, InviteStatus.expired, InviteStatus.rejected}:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite cannot be resent")
    invite.status = InviteStatus.pending
    invite.invite_token = invite.invite_token or uuid4().hex
    invite.expires_at = datetime.utcnow() + timedelta(hours=settings.invite_expiry_hours)
    invite.revoked_at = None
    invite.revoked_by_id = None
    invite.accepted_at = None
    invite.rejected_at = None
    db.commit()
    db.refresh(invite)
    log_event(
        db,
        project_id=invite.project_id,
        actor_id=current_user.id,
        event_type="invite_sent",
        entity_type="invite",
        entity_id=invite.id,
    )
    db.commit()
    return invite


@router.patch("/projects/{project_id}/members/{member_id}/role", response_model=ProjectMemberOut)
def update_member_role(
    project_id: int,
    member_id: int,
    payload: ProjectMemberRoleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMember:
    project = _get_project(db, project_id)
    if current_user.role.value != "faculty" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    member = db.get(ProjectMember, member_id)
    if not member or member.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    if member.user_id == project.owner_id and payload.role != MembershipRole.owner:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot demote project owner")
    member.role = payload.role
    db.commit()
    db.refresh(member)
    log_event(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        event_type="member_role_changed",
        entity_type="member",
        entity_id=member.id,
        metadata={"role": member.role.value},
    )
    db.commit()
    return member


@router.patch("/projects/{project_id}/members/{member_id}/status", response_model=ProjectMemberOut)
def update_member_status(
    project_id: int,
    member_id: int,
    payload: ProjectMemberStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProjectMember:
    project = _get_project(db, project_id)
    if current_user.role.value != "faculty" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    member = db.get(ProjectMember, member_id)
    if not member or member.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    if member.user_id == project.owner_id and payload.status != MemberStatus.active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot suspend project owner")
    member.status = payload.status
    db.commit()
    db.refresh(member)
    log_event(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        event_type="member_status_changed",
        entity_type="member",
        entity_id=member.id,
        metadata={"status": member.status.value},
    )
    db.commit()
    return member


@router.delete("/projects/{project_id}/members/{member_id}")
def remove_member(
    project_id: int,
    member_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict:
    project = _get_project(db, project_id)
    if current_user.role.value != "faculty" and project.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    member = db.get(ProjectMember, member_id)
    if not member or member.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    if member.user_id == project.owner_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot remove project owner")
    db.delete(member)
    db.commit()
    log_event(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        event_type="member_removed",
        entity_type="member",
        entity_id=member_id,
    )
    db.commit()
    return {"status": "removed"}
