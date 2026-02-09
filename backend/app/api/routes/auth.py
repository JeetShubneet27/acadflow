from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.core.config import settings
from app.models.enums import RoleEnum
from app.models.email_otp import EmailOTP
from app.models.user import User
from app.schemas.auth import LoginRequest, OtpChallenge, OtpResendRequest, OtpVerifyRequest, Token
from app.schemas.user import UserCreate, UserOut
from app.utils.email import send_email
from app.utils.otp import generate_otp_code, hash_otp


router = APIRouter(tags=["auth"])


def _create_otp(db: Session, user: User, purpose: str) -> EmailOTP:
    now = datetime.utcnow()
    existing = (
        db.query(EmailOTP)
        .filter(EmailOTP.email == user.email, EmailOTP.purpose == purpose, EmailOTP.consumed_at.is_(None))
        .order_by(EmailOTP.created_at.desc())
        .first()
    )
    if existing and existing.last_sent_at + timedelta(seconds=settings.otp_cooldown_seconds) > now:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="OTP recently sent")
    if existing:
        existing.consumed_at = now
        db.commit()

    code = generate_otp_code()
    otp = EmailOTP(
        user_id=user.id,
        email=user.email,
        purpose=purpose,
        otp_hash=hash_otp(user.email, purpose, code),
        created_at=now,
        expires_at=now + timedelta(minutes=settings.otp_expiry_minutes),
        last_sent_at=now,
    )
    db.add(otp)
    db.commit()
    db.refresh(otp)
    try:
        send_email(
            user.email,
            subject="AcadFlow verification code",
            body=f"Your AcadFlow verification code is {code}. It expires in {settings.otp_expiry_minutes} minutes.",
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to send OTP") from exc
    return otp


@router.post("/signup", response_model=OtpChallenge, status_code=status.HTTP_201_CREATED)
def signup(payload: UserCreate, db: Session = Depends(get_db)) -> OtpChallenge:
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        if not existing.is_email_verified:
            _create_otp(db, existing, purpose="signup")
            return OtpChallenge(
                email=existing.email,
                expires_in=settings.otp_expiry_minutes * 60,
            )
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
        is_email_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    _create_otp(db, user, purpose="signup")
    return OtpChallenge(email=user.email, expires_in=settings.otp_expiry_minutes * 60)


@router.post("/login", response_model=Token)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> Token:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if payload.role and user.role != payload.role:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Role mismatch")
    if not user.is_email_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")
    access_token = create_access_token(subject=str(user.id), role=user.role.value)
    return Token(access_token=access_token)


@router.post("/auth/otp/verify", response_model=Token)
def verify_otp(payload: OtpVerifyRequest, db: Session = Depends(get_db)) -> Token:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    otp = (
        db.query(EmailOTP)
        .filter(
            EmailOTP.email == payload.email,
            EmailOTP.purpose == "signup",
            EmailOTP.consumed_at.is_(None),
        )
        .order_by(EmailOTP.created_at.desc())
        .first()
    )
    purpose = "signup"
    if not otp:
        otp = (
            db.query(EmailOTP)
            .filter(
                EmailOTP.email == payload.email,
                EmailOTP.purpose == "login",
                EmailOTP.consumed_at.is_(None),
            )
            .order_by(EmailOTP.created_at.desc())
            .first()
        )
        purpose = "login"
    if not otp:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP not found")
    if otp.expires_at < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="OTP expired")
    if otp.attempts >= settings.otp_max_attempts:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="OTP attempts exceeded")

    is_valid = False
    if settings.otp_test_mode and payload.otp == settings.otp_test_code:
        is_valid = True
    elif hash_otp(payload.email, purpose, payload.otp) == otp.otp_hash:
        is_valid = True
    if not is_valid:
        otp.attempts += 1
        db.commit()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid OTP")

    otp.consumed_at = datetime.utcnow()
    otp.attempts = otp.attempts + 1
    if not user.is_email_verified:
        user.is_email_verified = True
        user.email_verified_at = datetime.utcnow()
    db.commit()
    access_token = create_access_token(subject=str(user.id), role=user.role.value)
    return Token(access_token=access_token)


@router.post("/auth/otp/resend", response_model=OtpChallenge)
def resend_otp(payload: OtpResendRequest, db: Session = Depends(get_db)) -> OtpChallenge:
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    _create_otp(db, user, purpose="signup")
    return OtpChallenge(email=user.email, expires_in=settings.otp_expiry_minutes * 60)


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)) -> User:
    return current_user
