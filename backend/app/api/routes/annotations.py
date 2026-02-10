from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.models.draft import Draft
from app.models.draft_annotation import DraftAnnotation
from app.models.enums import AnnotationStatus, MemberStatus
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.user import User
from app.schemas.annotation import AnnotationCreate, AnnotationOut, AnnotationUpdate
from app.utils.audit import log_event


router = APIRouter(tags=["annotations"])


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


def _ensure_owner_or_faculty(project: Project, user: User) -> None:
    if user.role.value == "faculty":
        return
    if project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


@router.post("/drafts/{draft_id}/annotations", response_model=AnnotationOut, status_code=status.HTTP_201_CREATED)
def create_annotation(
    draft_id: int,
    payload: AnnotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DraftAnnotation:
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    project = db.get(Project, draft.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_access(db, project, current_user)

    parent_id = payload.parent_id
    if parent_id:
        parent = db.get(DraftAnnotation, parent_id)
        if not parent or parent.draft_id != draft_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid parent annotation")

    annotation = DraftAnnotation(
        draft_id=draft_id,
        author_id=current_user.id,
        parent_id=parent_id,
        anchor_type=payload.anchor_type,
        anchor_data=payload.anchor_data,
        body=payload.body,
        status=AnnotationStatus.open,
    )
    db.add(annotation)
    db.commit()
    db.refresh(annotation)
    log_event(
        db,
        project_id=project.id,
        actor_id=current_user.id,
        event_type="annotation_created",
        entity_type="annotation",
        entity_id=annotation.id,
        metadata={"draft_id": draft_id},
    )
    db.commit()
    return annotation


@router.get("/drafts/{draft_id}/annotations", response_model=list[AnnotationOut])
def list_annotations(
    draft_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[DraftAnnotation]:
    draft = db.get(Draft, draft_id)
    if not draft:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Draft not found")
    project = db.get(Project, draft.project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_access(db, project, current_user)
    return (
        db.query(DraftAnnotation)
        .filter(DraftAnnotation.draft_id == draft_id)
        .order_by(DraftAnnotation.created_at.asc())
        .all()
    )


@router.patch("/annotations/{annotation_id}", response_model=AnnotationOut)
def update_annotation(
    annotation_id: int,
    payload: AnnotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DraftAnnotation:
    annotation = db.get(DraftAnnotation, annotation_id)
    if not annotation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annotation not found")
    draft = db.get(Draft, annotation.draft_id)
    project = db.get(Project, draft.project_id) if draft else None
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_access(db, project, current_user)
    if annotation.author_id != current_user.id and current_user.role.value != "faculty":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    annotation.body = payload.body
    annotation.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(annotation)
    log_event(
        db,
        project_id=project.id,
        actor_id=current_user.id,
        event_type="annotation_updated",
        entity_type="annotation",
        entity_id=annotation.id,
    )
    db.commit()
    return annotation


@router.post("/annotations/{annotation_id}/resolve", response_model=AnnotationOut)
def resolve_annotation(
    annotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DraftAnnotation:
    annotation = db.get(DraftAnnotation, annotation_id)
    if not annotation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annotation not found")
    draft = db.get(Draft, annotation.draft_id)
    project = db.get(Project, draft.project_id) if draft else None
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_owner_or_faculty(project, current_user)
    annotation.status = AnnotationStatus.resolved
    annotation.resolved_at = datetime.utcnow()
    annotation.resolved_by_id = current_user.id
    db.commit()
    db.refresh(annotation)
    log_event(
        db,
        project_id=project.id,
        actor_id=current_user.id,
        event_type="annotation_resolved",
        entity_type="annotation",
        entity_id=annotation.id,
    )
    db.commit()
    return annotation


@router.post("/annotations/{annotation_id}/reopen", response_model=AnnotationOut)
def reopen_annotation(
    annotation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DraftAnnotation:
    annotation = db.get(DraftAnnotation, annotation_id)
    if not annotation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annotation not found")
    draft = db.get(Draft, annotation.draft_id)
    project = db.get(Project, draft.project_id) if draft else None
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_owner_or_faculty(project, current_user)
    annotation.status = AnnotationStatus.open
    annotation.resolved_at = None
    annotation.resolved_by_id = None
    db.commit()
    db.refresh(annotation)
    log_event(
        db,
        project_id=project.id,
        actor_id=current_user.id,
        event_type="annotation_reopened",
        entity_type="annotation",
        entity_id=annotation.id,
    )
    db.commit()
    return annotation


@router.post("/annotations/{annotation_id}/replies", response_model=AnnotationOut, status_code=status.HTTP_201_CREATED)
def reply_annotation(
    annotation_id: int,
    payload: AnnotationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> DraftAnnotation:
    parent = db.get(DraftAnnotation, annotation_id)
    if not parent:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Annotation not found")
    draft = db.get(Draft, parent.draft_id)
    project = db.get(Project, draft.project_id) if draft else None
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_access(db, project, current_user)
    reply = DraftAnnotation(
        draft_id=parent.draft_id,
        author_id=current_user.id,
        parent_id=parent.id,
        anchor_type=parent.anchor_type,
        anchor_data=parent.anchor_data,
        body=payload.body,
        status=AnnotationStatus.open,
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)
    log_event(
        db,
        project_id=project.id,
        actor_id=current_user.id,
        event_type="annotation_replied",
        entity_type="annotation",
        entity_id=reply.id,
        metadata={"parent_id": parent.id},
    )
    db.commit()
    return reply
