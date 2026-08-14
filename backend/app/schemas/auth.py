import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole, UserStatus


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole
    status: UserStatus
    firm_id: uuid.UUID


class StaffCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=160)
    password: str = Field(min_length=8, max_length=128)
    role: UserRole = UserRole.FUNCIONARIO
    phone: str | None = Field(default=None, max_length=32)


class StaffUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=160)
    email: EmailStr | None = None
    role: UserRole | None = None
    status: UserStatus | None = None
    phone: str | None = Field(default=None, max_length=32)
    password: str | None = Field(default=None, min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshTokenRecord(BaseModel):
    token_id: uuid.UUID
    expires_at: datetime


class ClientInvitationCreate(BaseModel):
    email: EmailStr
    full_name: str


class ClientInvitationResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str
    expires_at: datetime


class ClientRegistration(BaseModel):
    invite_token: str
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    full_name: str = Field(min_length=2, max_length=160)
    phone: str | None = None


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(min_length=12, max_length=128)
