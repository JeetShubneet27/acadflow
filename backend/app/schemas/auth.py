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
