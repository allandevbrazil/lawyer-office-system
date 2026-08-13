import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.billing import InvoiceStatus


class InvoiceItemCreate(BaseModel):
    description: str = Field(min_length=2, max_length=240)
    quantity: Decimal = Field(gt=0)
    unit_price: Decimal = Field(ge=0)
    service_id: uuid.UUID | None = None


class InvoiceCreate(BaseModel):
    client_id: uuid.UUID
    case_id: uuid.UUID | None = None
    number: str = Field(min_length=2, max_length=40)
    description: str | None = Field(default=None, max_length=500)
    discount: Decimal = Field(default=Decimal("0.00"), ge=0)
    due_date: date
    items: list[InvoiceItemCreate] = Field(min_length=1)


class InvoiceStatusUpdate(BaseModel):
    status: InvoiceStatus


class InvoiceItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    description: str
    quantity: Decimal
    unit_price: Decimal
    amount: Decimal


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    firm_id: uuid.UUID
    client_id: uuid.UUID
    case_id: uuid.UUID | None
    number: str
    description: str | None
    subtotal: Decimal
    discount: Decimal
    total: Decimal
    due_date: date
    paid_at: datetime | None
    status: InvoiceStatus
    issued_at: datetime
    items: list[InvoiceItemResponse] = []
