from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db, require_roles
from app.models.enums import ReviewStatus, RoleEnum
from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.review import Review
from app.models.user import User
from app.schemas.review import ReviewAssign, ReviewOut, ReviewSubmit


router = APIRouter(tags=["reviews"])


def _ensure_owner_or_faculty(db: Session, project: Project, user: User) -> None:
    if user.role.value == "faculty":
        return
    if project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")


def _ensure_member_or_owner(db: Session, project: Project, user: User) -> None:
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


@router.post("/projects/{project_id}/reviews/assign", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def assign_reviewer(
    project_id: int,
    payload: ReviewAssign,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(["faculty"])),
) -> Review:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    reviewer = db.get(User, payload.reviewer_id)
    if not reviewer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reviewer not found")
    if reviewer.role != RoleEnum.reviewer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User is not a reviewer")
    existing = (
        db.query(Review)
        .filter(Review.project_id == project_id, Review.reviewer_id == payload.reviewer_id)
        .first()
    )
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reviewer already assigned")
    review = Review(project_id=project_id, reviewer_id=payload.reviewer_id)
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/reviews/assigned", response_model=list[ReviewOut])
def list_assigned_reviews(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Review]:
    if current_user.role != RoleEnum.reviewer:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    return (
        db.query(Review)
        .filter(Review.reviewer_id == current_user.id)
        .order_by(Review.created_at.desc())
        .all()
    )


@router.put("/reviews/{review_id}", response_model=ReviewOut)
def submit_review(
    review_id: int,
    payload: ReviewSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Review:
    review = db.get(Review, review_id)
    if not review:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Review not found")
    if review.reviewer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    review.score = payload.score
    review.comments = payload.comments
    review.status = ReviewStatus.submitted
    review.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(review)
    return review


@router.get("/projects/{project_id}/reviews", response_model=list[ReviewOut])
def list_project_reviews(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Review]:
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    _ensure_member_or_owner(db, project, current_user)
    return db.query(Review).filter(Review.project_id == project_id).order_by(Review.created_at.desc()).all()
