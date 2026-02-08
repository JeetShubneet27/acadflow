from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, require_roles
from app.core.config import settings
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.user import UserOut, UserRoleUpdate


router = APIRouter(tags=["users"])


@router.put("/users/{user_id}/role", response_model=UserOut)
def update_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(["faculty"])),
) -> User:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if payload.role == RoleEnum.reviewer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reviewer role is reserved for faculty members",
        )
    if payload.role == RoleEnum.faculty:
        domain = user.email.split("@")[-1].lower()
        blocked = {item.strip().lower() for item in settings.faculty_blocked_domains.split(",") if item.strip()}
        if domain in blocked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Faculty role requires an official institutional email",
            )
    user.role = payload.role
    db.commit()
    db.refresh(user)
    return user
