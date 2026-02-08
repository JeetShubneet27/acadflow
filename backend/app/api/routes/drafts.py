from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.draft import Draft
from app.models.draft_lock import DraftLock
from app.models.enums import DraftLockStatus, MemberStatus
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.draft import DraftOut
from app.schemas.draft_lock import DraftLockOut
from app.utils.audit import log_event
from app.utils.files import save_upload_file, validate_upload_file


router = APIRouter(tags=["drafts"])


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
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


@router.post("/projects/{project_id}/drafts", response_model=DraftOut, status_code=status.HTTP_201_CREATED)
def upload_draft(
    project_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Draft:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_access(db, project, current_user)

    validate_upload_file(file)
    latest_version = (
        db.query(func.max(Draft.version))
        .filter(Draft.project_id == project_id)
        .scalar()
        or 0
    )
    if latest_version:
        latest_draft = (
            db.query(Draft)
            .filter(Draft.project_id == project_id, Draft.version == latest_version)
            .first()
        )
        if latest_draft:
            lock = (
                db.query(DraftLock)
                .filter(
                    DraftLock.draft_id == latest_draft.id,
                    DraftLock.status == DraftLockStatus.active,
                )
                .order_by(DraftLock.locked_at.desc())
                .first()
            )
            if lock and lock.expires_at < datetime.utcnow():
                lock.status = DraftLockStatus.expired
                db.commit()
                lock = None
            if lock and lock.locked_by_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Draft is locked by another collaborator",
                )
    storage_dir = f"{settings.storage_dir}/drafts"
    file_path, original_filename = save_upload_file(file, storage_dir, f"draft-{project_id}")

    draft = Draft(
        project_id=project_id,
        version=latest_version + 1,
        file_path=file_path,
        original_filename=original_filename,
        uploaded_by_id=current_user.id,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    log_event(
        db,
        project_id=project_id,
        actor_id=current_user.id,
        event_type="draft_uploaded",
        entity_type="draft",
        entity_id=draft.id,
        metadata={"version": draft.version, "filename": draft.original_filename},
    )
    db.commit()
    return draft


@router.get("/projects/{project_id}/drafts", response_model=list[DraftOut])
def list_drafts(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Draft]:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_access(db, project, current_user)
    return db.query(Draft).filter(Draft.project_id == project_id).order_by(Draft.version.desc()).all()


@router.get("/drafts/{draft_id}/download")
def download_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    project = db.get(Project, draft.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_access(db, project, current_user)
    if not draft.file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File missing")
    return FileResponse(draft.file_path, filename=draft.original_filename)


@router.post("/drafts/{draft_id}/lock", response_model=DraftLockOut, status_code=status.HTTP_201_CREATED)
def lock_draft(
    draft_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DraftLock:
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    project = db.get(Project, draft.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_access(db, project, current_user)

    lock = (
        db.query(DraftLock)
        .filter(DraftLock.draft_id == draft_id, DraftLock.status == DraftLockStatus.active)
        .order_by(DraftLock.locked_at.desc())
        .first()
    )
    if lock and lock.expires_at < datetime.utcnow():
        lock.status = DraftLockStatus.expired
        db.commit()
        lock = None
    if lock:
        if lock.locked_by_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Draft already locked")
        return lock

    expires_at = datetime.utcnow() + timedelta(minutes=settings.draft_lock_minutes)
    lock = DraftLock(
        draft_id=draft_id,
        locked_by_id=current_user.id,
        status=DraftLockStatus.active,
        expires_at=expires_at,
    )
    db.add(lock)
    db.commit()
    db.refresh(lock)
    log_event(
        db,
        project_id=project.id,
        actor_id=current_user.id,
        event_type="draft_locked",
        entity_type="draft",
        entity_id=draft_id,
        metadata={"expires_at": lock.expires_at.isoformat()},
    )
    db.commit()
    return lock


@router.get("/drafts/{draft_id}/lock", response_model=DraftLockOut)
def get_lock(
    draft_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DraftLock:
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    project = db.get(Project, draft.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_access(db, project, current_user)
    lock = (
        db.query(DraftLock)
        .filter(DraftLock.draft_id == draft_id, DraftLock.status == DraftLockStatus.active)
        .order_by(DraftLock.locked_at.desc())
        .first()
    )
    if not lock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active lock")
    if lock.expires_at < datetime.utcnow():
        lock.status = DraftLockStatus.expired
        db.commit()
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active lock")
    return lock


@router.delete("/drafts/{draft_id}/lock", response_model=DraftLockOut)
def release_lock(
    draft_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DraftLock:
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    project = db.get(Project, draft.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_access(db, project, current_user)
    lock = (
        db.query(DraftLock)
        .filter(DraftLock.draft_id == draft_id, DraftLock.status == DraftLockStatus.active)
        .order_by(DraftLock.locked_at.desc())
        .first()
    )
    if not lock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active lock")
    if lock.locked_by_id != current_user.id and current_user.role.value != "faculty":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    lock.status = DraftLockStatus.released
    lock.released_at = datetime.utcnow()
    db.commit()
    db.refresh(lock)
    log_event(
        db,
        project_id=project.id,
        actor_id=current_user.id,
        event_type="draft_lock_released",
        entity_type="draft",
        entity_id=draft_id,
    )
    db.commit()
    return lock
