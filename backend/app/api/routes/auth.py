from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.core.config import settings
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.auth import LoginRequest, Token
from app.schemas.user import UserCreate, UserOut


router = APIRouter(tags=["auth"])


@router.post("/signup", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, db: Session = Depends(get_db)) -> User:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    role = payload.role or RoleEnum.student
    if role == RoleEnum.reviewer:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reviewer role is not available")
    if role == RoleEnum.faculty:
        domain = payload.email.split("@")[-1].lower()
        blocked = {item.strip().lower() for item in settings.faculty_blocked_domains.split(",") if item.strip()}
        if domain in blocked:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Faculty role requires an official institutional email",
            )
    user = User(
        email=payload.email,
        full_name=payload.full_name,
        hashed_password=hash_password(payload.password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if payload.role and user.role != payload.role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role mismatch")
    access_token = create_access_token(subject=str(user.id), role=user.role.value)
    return Token(access_token=access_token)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
