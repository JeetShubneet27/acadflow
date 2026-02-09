from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.enums import RoleEnum


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    role: Optional[RoleEnum] = None


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class OtpChallenge(BaseModel):
    otp_required: bool = True
    email: EmailStr
    expires_in: int


class OtpVerifyRequest(BaseModel):
    email: EmailStr
    otp: str


class OtpResendRequest(BaseModel):
    email: EmailStr
