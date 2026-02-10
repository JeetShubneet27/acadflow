from datetime import datetime

from typing import Optional

from pydantic import BaseModel, EmailStr

from app.models.enums import RoleEnum


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: RoleEnum
    is_email_verified: bool
    bio: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    research_interests: Optional[str] = None
    website: Optional[str] = None
    orcid: Optional[str] = None
    linkedin: Optional[str] = None

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str
    role: Optional[RoleEnum] = None


class UserRoleUpdate(BaseModel):
    role: RoleEnum


class UserProfileUpdate(BaseModel):
    bio: Optional[str] = None
    institution: Optional[str] = None
    department: Optional[str] = None
    research_interests: Optional[str] = None
    website: Optional[str] = None
    orcid: Optional[str] = None
    linkedin: Optional[str] = None


class UserOut(UserBase):
    id: int
    created_at: datetime
