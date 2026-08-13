from decimal import Decimal

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db import get_db_session
from app.models import Case, CaseStatus, Client, Invoice, InvoiceStatus, User, UserRole

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", summary="Get authorized dashboard metrics")
async def summary(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, object]:
    case_query = select(func.count(Case.id)).where(
        Case.firm_id == current_user.firm_id, Case.status == CaseStatus.ACTIVE
    )
    invoice_query = select(func.count(Invoice.id)).where(
        Invoice.firm_id == current_user.firm_id,
        Invoice.status.in_([InvoiceStatus.PENDING, InvoiceStatus.OVERDUE]),
    )
    total_query = select(func.coalesce(func.sum(Invoice.total), Decimal("0.00"))).where(
        Invoice.firm_id == current_user.firm_id, Invoice.status == InvoiceStatus.PAID
    )
    if current_user.role == UserRole.CLIENTE:
        case_query = case_query.join(Client, Client.id == Case.client_id).where(
            Client.user_id == current_user.id
        )
        invoice_query = invoice_query.join(Client, Client.id == Invoice.client_id).where(
            Client.user_id == current_user.id
        )
        total_query = total_query.join(Client, Client.id == Invoice.client_id).where(
            Client.user_id == current_user.id
        )
    return {
        "active_cases": int(await session.scalar(case_query) or 0),
        "pending_invoices": int(await session.scalar(invoice_query) or 0),
        "billing_total": str(await session.scalar(total_query) or Decimal("0.00")),
    }
