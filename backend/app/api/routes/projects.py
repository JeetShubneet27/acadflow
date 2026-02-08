from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.enums import InviteStatus, MembershipRole, ProjectVisibility
from app.models.project import Project
from app.models.project_invite import ProjectInvite
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.invite import InviteAction, InviteCreate, InviteOut
from app.schemas.project import ProjectCreate, ProjectMemberOut, ProjectOut, ProjectVisibilityUpdate


router = APIRouter(tags=["projects"])


def _get_project(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def _is_project_member(db: Session, project_id: int, user_id: int) -> bool:
    return (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        .first()
        is not None
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
        .filter(or_(Project.owner_id == current_user.id, ProjectMember.user_id == current_user.id))
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
            ProjectInvite.status == InviteStatus.pending,
        )
        .first()
    )
    if existing_invite:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite already pending")

    invite = ProjectInvite(
        project_id=project_id,
        inviter_id=current_user.id,
        invitee_id=invitee.id,
        status=InviteStatus.pending,
        membership_role=payload.membership_role,
    )
    db.add(invite)
    db.commit()
    db.refresh(invite)
    return invite


@router.get("/projects/invites", response_model=list[InviteOut])
def list_invites(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ProjectInvite]:
    return (
        db.query(ProjectInvite)
        .filter(ProjectInvite.invitee_id == current_user.id)
        .order_by(ProjectInvite.created_at.desc())
        .all()
    )


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
        )
        db.add(member)
    invite.status = payload.status
    db.commit()
    db.refresh(invite)
    return invite
