import uuid
from datetime import UTC, datetime
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Case, Client, Invoice, InvoiceItem, InvoiceStatus, Service, User, UserRole
from app.schemas.billing import InvoiceCreate, InvoiceStatusUpdate

CENT = Decimal("0.01")


class BillingService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_invoices(self, current_user: User) -> list[Invoice]:
        query = select(Invoice).options(selectinload(Invoice.items)).where(
            Invoice.firm_id == current_user.firm_id
        )
        if current_user.role == UserRole.CLIENTE:
            query = query.join(Client, Client.id == Invoice.client_id).where(
                Client.user_id == current_user.id
            )
        return list((await self.session.scalars(query.order_by(Invoice.due_date.desc()))).all())

    async def create_invoice(self, payload: InvoiceCreate, current_user: User) -> Invoice:
        if current_user.role == UserRole.CLIENTE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff role required")
        client = await self.session.scalar(
            select(Client).where(
                Client.id == payload.client_id, Client.firm_id == current_user.firm_id
            )
        )
        if not client:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Client not found")
        if payload.case_id:
            case = await self.session.scalar(
                select(Case).where(
                    Case.id == payload.case_id,
                    Case.firm_id == current_user.firm_id,
                    Case.client_id == payload.client_id,
                )
            )
            if not case:
                raise HTTPException(status_code=404, detail="Case not found for client")
        for item in payload.items:
            if item.service_id:
                service = await self.session.scalar(
                    select(Service).where(
                        Service.id == item.service_id,
                        Service.firm_id == current_user.firm_id,
                        Service.client_id == payload.client_id,
                    )
                )
                if not service:
                    raise HTTPException(status_code=404, detail="Service not found for client")
        items = [
            InvoiceItem(
                description=item.description,
                quantity=item.quantity,
                unit_price=item.unit_price,
                amount=(item.quantity * item.unit_price).quantize(CENT, rounding=ROUND_HALF_UP),
                service_id=item.service_id,
            )
            for item in payload.items
        ]
        subtotal = sum((item.amount for item in items), Decimal("0.00"))
        discount = payload.discount.quantize(CENT, rounding=ROUND_HALF_UP)
        if discount > subtotal:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Discount exceeds subtotal",
            )
        invoice = Invoice(
            firm_id=current_user.firm_id,
            client_id=payload.client_id,
            case_id=payload.case_id,
            number=payload.number,
            description=payload.description,
            subtotal=subtotal,
            discount=discount,
            total=(subtotal - discount).quantize(CENT, rounding=ROUND_HALF_UP),
            due_date=payload.due_date,
            issued_at=datetime.now(UTC),
            items=items,
        )
        self.session.add(invoice)
        await self.session.commit()
        return await self.get_invoice(invoice.id, current_user)

    async def get_invoice(self, invoice_id: uuid.UUID, current_user: User) -> Invoice:
        query = select(Invoice).options(selectinload(Invoice.items)).where(
            Invoice.id == invoice_id, Invoice.firm_id == current_user.firm_id
        )
        if current_user.role == UserRole.CLIENTE:
            query = query.join(Client, Client.id == Invoice.client_id).where(
                Client.user_id == current_user.id
            )
        invoice = await self.session.scalar(query)
        if not invoice:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invoice not found")
        return invoice

    async def update_status(
        self, invoice_id: uuid.UUID, payload: InvoiceStatusUpdate, current_user: User
    ) -> Invoice:
        if current_user.role == UserRole.CLIENTE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff role required")
        invoice = await self.get_invoice(invoice_id, current_user)
        invoice.status = payload.status
        invoice.paid_at = datetime.now(UTC) if payload.status == InvoiceStatus.PAID else None
        await self.session.commit()
        return await self.get_invoice(invoice_id, current_user)

    async def delete_invoice(self, invoice_id: uuid.UUID, current_user: User) -> None:
        if current_user.role == UserRole.CLIENTE:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff role required")
        invoice = await self.get_invoice(invoice_id, current_user)
        await self.session.execute(delete(Invoice).where(Invoice.id == invoice.id))
        await self.session.commit()
