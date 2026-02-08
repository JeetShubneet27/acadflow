from app.db.session import SessionLocal
from app.models.enums import RoleEnum
from app.models.user import User


def set_user_role(email: str, role: RoleEnum) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.role = role
            db.commit()
    finally:
        db.close()
