from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.draft import Draft
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.draft import DraftOut
from app.utils.files import save_upload_file


router = APIRouter(tags=["drafts"])


def _ensure_access(db: Session, project: Project, user: User) -> None:
    if user.role.value == "faculty":
        return
    is_member = (
        db.query(ProjectMember)
        .filter(ProjectMember.project_id == project.id, ProjectMember.user_id == user.id)
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

    latest_version = (
        db.query(func.max(Draft.version))
        .filter(Draft.project_id == project_id)
        .scalar()
        or 0
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
