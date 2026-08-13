import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.case import CaseStatus


class CaseCreate(BaseModel):
    client_id: uuid.UUID
    title: str = Field(min_length=3, max_length=240)
    description: str | None = Field(default=None, max_length=4000)
    case_number: str | None = Field(default=None, max_length=64)
    court: str | None = Field(default=None, max_length=200)
    jurisdiction: str | None = Field(default=None, max_length=160)
    case_type: str | None = Field(default=None, max_length=120)
    priority: str = Field(default="NORMAL", pattern="^(LOW|NORMAL|HIGH|URGENT)$")


class CaseUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=3, max_length=240)
    description: str | None = Field(default=None, max_length=4000)
    status: CaseStatus | None = None
    priority: str | None = Field(default=None, pattern="^(LOW|NORMAL|HIGH|URGENT)$")
    responsible_user_id: uuid.UUID | None = None


class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    firm_id: uuid.UUID
    client_id: uuid.UUID
    responsible_user_id: uuid.UUID | None
    case_number: str | None
    title: str
    description: str | None
    court: str | None
    jurisdiction: str | None
    case_type: str | None
    status: CaseStatus
    priority: str
    opened_at: datetime
    closed_at: datetime | None


class CaseEventCreate(BaseModel):
    event_type: str
    title: str
    description: str | None = None
    occurred_at: datetime
    visibility: str = "INTERNAL"


class CaseEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    case_id: uuid.UUID
    author_user_id: uuid.UUID
    event_type: str
    title: str
    description: str | None
    occurred_at: datetime
    visibility: str
