from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.models.enums import RoleEnum


class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: RoleEnum

    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str
    password: str


class UserRoleUpdate(BaseModel):
    role: RoleEnum


class UserOut(UserBase):
    id: int
    created_at: datetime
