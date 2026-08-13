import uuid

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.client import ClientStatus, ClientType


class ClientCreate(BaseModel):
    type: ClientType
    name: str = Field(min_length=2, max_length=200)
    document_number: str | None = Field(default=None, max_length=128)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=4000)


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=200)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=32)
    notes: str | None = Field(default=None, max_length=4000)
    status: ClientStatus | None = None


class ClientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    firm_id: uuid.UUID
    user_id: uuid.UUID | None
    type: ClientType
    name: str
    document_number: str | None
    email: EmailStr | None
    phone: str | None
    notes: str | None
    status: ClientStatus
