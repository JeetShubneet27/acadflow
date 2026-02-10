from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.models.conference import Conference
from app.models.user import User
from app.schemas.conference import ConferenceCreate, ConferenceOut


router = APIRouter(tags=["conferences"])


@router.get("/conferences", response_model=list[ConferenceOut])
def list_conferences(
    q: str = Query("", max_length=80),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
) -> list[Conference]:
    query = db.query(Conference)
    if q:
        q_like = f"%{q.lower()}%"
        query = query.filter(
            or_(
                Conference.title.ilike(q_like),
                Conference.location.ilike(q_like),
                Conference.description.ilike(q_like),
            )
        )
    return (
        query.order_by(
            Conference.submission_deadline.is_(None),
            Conference.submission_deadline.asc(),
            Conference.start_date.asc(),
        )
        .limit(limit)
        .all()
    )


@router.post("/conferences", response_model=ConferenceOut, status_code=status.HTTP_201_CREATED)
def create_conference(
    payload: ConferenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["faculty"])),
) -> Conference:
    conference = Conference(
        title=payload.title,
        website=str(payload.website) if payload.website else None,
        location=payload.location,
        start_date=payload.start_date,
        end_date=payload.end_date,
        submission_deadline=payload.submission_deadline,
        description=payload.description,
        created_by_id=current_user.id,
    )
    db.add(conference)
    db.commit()
    db.refresh(conference)
    return conference


@router.delete("/conferences/{conference_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conference(
    conference_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(["faculty"])),
):
    conference = db.get(Conference, conference_id)
    if not conference:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conference not found")
    db.delete(conference)
    db.commit()
    return None
