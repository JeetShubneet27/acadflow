from app.db.session import SessionLocal
from app.models.enums import RoleEnum
from app.models.user import User


OTP_TEST_CODE = "123456"


def set_user_role(email: str, role: RoleEnum) -> None:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.role = role
            db.commit()
    finally:
        db.close()


def get_user_id(email: str) -> int:
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise ValueError("User not found")
        return user.id
    finally:
        db.close()


def verify_otp(client, email: str) -> str:
    response = client.post("/auth/otp/verify", json={"email": email, "otp": OTP_TEST_CODE})
    assert response.status_code == 200
    return response.json()["access_token"]
