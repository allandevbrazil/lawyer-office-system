import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db import get_db_session
from app.models import User
from app.schemas.billing import InvoiceCreate, InvoiceResponse, InvoiceStatusUpdate
from app.services.billing_service import BillingService

router = APIRouter(prefix="/invoices", tags=["billing"])


@router.get("", response_model=list[InvoiceResponse], summary="List invoices")
async def list_invoices(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    status_filter: str | None = Query(default=None, alias="status"),
) -> list[InvoiceResponse]:
    invoices = await BillingService(session).list_invoices(current_user)
    if status_filter:
        invoices = [invoice for invoice in invoices if invoice.status.value == status_filter]
    return [InvoiceResponse.model_validate(invoice) for invoice in invoices]


@router.post("", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
async def create_invoice(
    payload: InvoiceCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> InvoiceResponse:
    invoice = await BillingService(session).create_invoice(payload, current_user)
    return InvoiceResponse.model_validate(invoice)


@router.get("/{invoice_id}", response_model=InvoiceResponse)
async def get_invoice(
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> InvoiceResponse:
    invoice = await BillingService(session).get_invoice(invoice_id, current_user)
    return InvoiceResponse.model_validate(invoice)


@router.patch("/{invoice_id}", response_model=InvoiceResponse)
async def update_invoice_status(
    invoice_id: uuid.UUID,
    payload: InvoiceStatusUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> InvoiceResponse:
    invoice = await BillingService(session).update_status(invoice_id, payload, current_user)
    return InvoiceResponse.model_validate(invoice)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_invoice(
    invoice_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> None:
    await BillingService(session).delete_invoice(invoice_id, current_user)
