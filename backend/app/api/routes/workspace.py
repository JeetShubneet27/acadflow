from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.enums import DraftLockStatus, MemberStatus, WorkspaceFormat
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.models.workspace_document import WorkspaceDocument
from app.models.workspace_lock import WorkspaceLock
from app.models.workspace_revision import WorkspaceRevision
from app.schemas.workspace import (
    WorkspaceDocumentCreate,
    WorkspaceDocumentOut,
    WorkspaceLatexUpdate,
    WorkspaceLockOut,
    WorkspaceRevisionOut,
)
from app.utils.audit import log_event
from app.utils.files import save_upload_file


router = APIRouter(tags=["workspace"])


def _ensure_project_access(db: Session, project: Project, user: User) -> None:
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


def _validate_word_upload(upload: UploadFile) -> None:
    filename = upload.filename or ""
    ext = Path(filename).suffix.lower()
    if ext not in {".doc", ".docx"}:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unsupported file type. Upload DOC or DOCX.",
        )


def _latest_revision(db: Session, document_id: int) -> Optional[WorkspaceRevision]:
    return (
        db.query(WorkspaceRevision)
        .filter(WorkspaceRevision.document_id == document_id)
        .order_by(WorkspaceRevision.version.desc())
        .first()
    )


def _document_out(
    doc: WorkspaceDocument, latest: Optional[WorkspaceRevision]
) -> WorkspaceDocumentOut:
    return WorkspaceDocumentOut(
        id=doc.id,
        project_id=doc.project_id,
        title=doc.title,
        format=doc.format,
        created_by_id=doc.created_by_id,
        created_at=doc.created_at,
        updated_at=doc.updated_at,
        latest_version=latest.version if latest else None,
        latest_updated_at=latest.created_at if latest else None,
    )


def _get_active_lock(db: Session, document_id: int) -> Optional[WorkspaceLock]:
    lock = (
        db.query(WorkspaceLock)
        .filter(
            WorkspaceLock.document_id == document_id,
            WorkspaceLock.status == DraftLockStatus.active,
        )
        .order_by(WorkspaceLock.locked_at.desc())
        .first()
    )
    if lock and lock.expires_at <= datetime.utcnow():
        lock.status = DraftLockStatus.expired
        db.commit()
        db.refresh(lock)
        return None
    return lock


@router.get("/projects/{project_id}/workspace/documents", response_model=list[WorkspaceDocumentOut])
def list_documents(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WorkspaceDocumentOut]:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_project_access(db, project, current_user)
    documents = (
        db.query(WorkspaceDocument)
        .filter(WorkspaceDocument.project_id == project_id)
        .order_by(WorkspaceDocument.updated_at.desc())
        .all()
    )
    return [_document_out(doc, _latest_revision(db, doc.id)) for doc in documents]


@router.post(
    "/projects/{project_id}/workspace/documents/latex",
    response_model=WorkspaceDocumentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_latex_document(
    project_id: int,
    payload: WorkspaceDocumentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceDocumentOut:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_project_access(db, project, current_user)

    document = WorkspaceDocument(
        project_id=project_id,
        title=payload.title,
        format=WorkspaceFormat.latex,
        created_by_id=current_user.id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    revision = WorkspaceRevision(
        document_id=document.id,
        version=1,
        content_text=payload.content or "",
        created_by_id=current_user.id,
    )
    document.updated_at = datetime.utcnow()
    db.add(revision)
    db.commit()
    db.refresh(revision)

    log_event(db, project_id, current_user.id, "workspace_document_created", {"document_id": document.id})
    return _document_out(document, revision)


@router.post(
    "/projects/{project_id}/workspace/documents/word",
    response_model=WorkspaceDocumentOut,
    status_code=status.HTTP_201_CREATED,
)
def create_word_document(
    project_id: int,
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceDocumentOut:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_project_access(db, project, current_user)
    _validate_word_upload(file)

    document = WorkspaceDocument(
        project_id=project_id,
        title=title,
        format=WorkspaceFormat.word,
        created_by_id=current_user.id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    storage_dir = f"{settings.storage_dir}/workspace"
    file_path, original_filename = save_upload_file(file, storage_dir, f"workspace-{document.id}-v1")
    revision = WorkspaceRevision(
        document_id=document.id,
        version=1,
        file_path=file_path,
        original_filename=original_filename,
        created_by_id=current_user.id,
    )
    document.updated_at = datetime.utcnow()
    db.add(revision)
    db.commit()
    db.refresh(revision)

    log_event(db, project_id, current_user.id, "workspace_document_created", {"document_id": document.id})
    return _document_out(document, revision)


@router.get("/workspace/documents/{document_id}/revisions", response_model=list[WorkspaceRevisionOut])
def list_revisions(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[WorkspaceRevision]:
    document = db.get(WorkspaceDocument, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    project = db.get(Project, document.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_project_access(db, project, current_user)
    return (
        db.query(WorkspaceRevision)
        .filter(WorkspaceRevision.document_id == document_id)
        .order_by(WorkspaceRevision.version.desc())
        .all()
    )


@router.get("/workspace/documents/{document_id}/latex", response_model=WorkspaceLatexUpdate)
def get_latex_content(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceLatexUpdate:
    document = db.get(WorkspaceDocument, document_id)
    if not document or document.format != WorkspaceFormat.latex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    project = db.get(Project, document.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_project_access(db, project, current_user)
    latest = _latest_revision(db, document_id)
    return WorkspaceLatexUpdate(content=latest.content_text if latest else "")


@router.put("/workspace/documents/{document_id}/latex", response_model=WorkspaceRevisionOut)
def update_latex_content(
    document_id: int,
    payload: WorkspaceLatexUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceRevision:
    document = db.get(WorkspaceDocument, document_id)
    if not document or document.format != WorkspaceFormat.latex:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    project = db.get(Project, document.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_project_access(db, project, current_user)

    lock = _get_active_lock(db, document_id)
    if lock and lock.locked_by_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document is locked")

    latest = _latest_revision(db, document_id)
    revision = WorkspaceRevision(
        document_id=document.id,
        version=(latest.version + 1) if latest else 1,
        content_text=payload.content,
        created_by_id=current_user.id,
    )
    document.updated_at = datetime.utcnow()
    db.add(revision)
    db.commit()
    db.refresh(revision)

    log_event(db, project.id, current_user.id, "workspace_latex_updated", {"document_id": document.id})
    return revision


@router.post("/workspace/documents/{document_id}/revisions", response_model=WorkspaceRevisionOut)
def upload_word_revision(
    document_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceRevision:
    document = db.get(WorkspaceDocument, document_id)
    if not document or document.format != WorkspaceFormat.word:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    project = db.get(Project, document.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_project_access(db, project, current_user)
    _validate_word_upload(file)

    lock = _get_active_lock(db, document_id)
    if lock and lock.locked_by_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document is locked")

    latest = _latest_revision(db, document_id)
    version = (latest.version + 1) if latest else 1
    storage_dir = f"{settings.storage_dir}/workspace"
    file_path, original_filename = save_upload_file(file, storage_dir, f"workspace-{document.id}-v{version}")
    revision = WorkspaceRevision(
        document_id=document.id,
        version=version,
        file_path=file_path,
        original_filename=original_filename,
        created_by_id=current_user.id,
    )
    document.updated_at = datetime.utcnow()
    db.add(revision)
    db.commit()
    db.refresh(revision)

    log_event(db, project.id, current_user.id, "workspace_revision_uploaded", {"document_id": document.id})
    return revision


@router.get("/workspace/revisions/{revision_id}/download")
def download_revision(
    revision_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    revision = db.get(WorkspaceRevision, revision_id)
    if not revision:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Revision not found")
    document = db.get(WorkspaceDocument, revision.document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    project = db.get(Project, document.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_project_access(db, project, current_user)
    if document.format == WorkspaceFormat.latex:
        return {"content": revision.content_text or ""}
    if not revision.file_path:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not available")
    return FileResponse(revision.file_path, filename=revision.original_filename)


@router.post("/workspace/documents/{document_id}/lock", response_model=WorkspaceLockOut)
def lock_document(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceLock:
    document = db.get(WorkspaceDocument, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    project = db.get(Project, document.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_project_access(db, project, current_user)

    existing = _get_active_lock(db, document_id)
    if existing:
        if existing.locked_by_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Document is locked")
        return existing

    expires_at = datetime.utcnow() + timedelta(minutes=settings.draft_lock_minutes)
    lock = WorkspaceLock(
        document_id=document_id,
        locked_by_id=current_user.id,
        status=DraftLockStatus.active,
        expires_at=expires_at,
    )
    db.add(lock)
    db.commit()
    db.refresh(lock)

    log_event(db, project.id, current_user.id, "workspace_lock_acquired", {"document_id": document.id})
    return lock


@router.get("/workspace/documents/{document_id}/lock", response_model=WorkspaceLockOut)
def get_document_lock(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceLock:
    document = db.get(WorkspaceDocument, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    project = db.get(Project, document.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_project_access(db, project, current_user)
    lock = _get_active_lock(db, document_id)
    if not lock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active lock")
    return lock


@router.delete("/workspace/documents/{document_id}/lock", response_model=WorkspaceLockOut)
def release_document_lock(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> WorkspaceLock:
    document = db.get(WorkspaceDocument, document_id)
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    project = db.get(Project, document.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_project_access(db, project, current_user)

    lock = _get_active_lock(db, document_id)
    if not lock:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No active lock")
    if lock.locked_by_id != current_user.id and current_user.role.value != "faculty":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    lock.status = DraftLockStatus.released
    lock.released_at = datetime.utcnow()
    db.commit()
    db.refresh(lock)

    log_event(db, project.id, current_user.id, "workspace_lock_released", {"document_id": document.id})
    return lock
