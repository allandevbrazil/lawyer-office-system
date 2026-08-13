import uuid
from decimal import Decimal

import httpx
import pytest

from app.core.security import hash_password
from app.db import async_session_factory, engine
from app.main import app
from app.models import Client, Firm, User, UserRole, UserStatus


@pytest.fixture(autouse=True)
async def dispose_database_engine() -> None:
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_invoice_totals_status_and_client_scope() -> None:
    staff_email = f"billing-staff-{uuid.uuid4()}@example.com"
    client_email = f"billing-client-{uuid.uuid4()}@example.com"
    password = "billing-test-password-123"

    async with async_session_factory() as session:
        firm = Firm(name="Billing Test Firm")
        session.add(firm)
        await session.flush()
        staff = User(
            firm_id=firm.id,
            email=staff_email,
            password_hash=hash_password(password),
            full_name="Billing Staff",
            role=UserRole.MASTER,
            status=UserStatus.ACTIVE,
        )
        client_user = User(
            firm_id=firm.id,
            email=client_email,
            password_hash=hash_password(password),
            full_name="Billing Client",
            role=UserRole.CLIENTE,
            status=UserStatus.ACTIVE,
        )
        session.add_all([staff, client_user])
        await session.flush()
        client = Client(
            firm_id=firm.id,
            user_id=client_user.id,
            type="PF",
            name="Billing Client",
            email=client_email,
        )
        session.add(client)
        await session.commit()
        client_id = client.id

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http_client:
        staff_login = await http_client.post(
            "/api/v1/auth/token", data={"username": staff_email, "password": password}
        )
        staff_token = staff_login.json()["access_token"]
        created = await http_client.post(
            "/api/v1/invoices",
            headers={"Authorization": f"Bearer {staff_token}"},
            json={
                "client_id": str(client_id),
                "number": "FAT-001",
                "due_date": "2026-09-01",
                "discount": "10.00",
                "items": [
                    {"description": "Consulta", "quantity": "2", "unit_price": "75.00"},
                    {"description": "Peticao", "quantity": "1", "unit_price": "100.00"},
                ],
            },
        )
        assert created.status_code == 201
        invoice = created.json()
        assert Decimal(invoice["subtotal"]) == Decimal("250.00")
        assert Decimal(invoice["total"]) == Decimal("240.00")

        paid = await http_client.patch(
            f"/api/v1/invoices/{invoice['id']}",
            headers={"Authorization": f"Bearer {staff_token}"},
            json={"status": "PAID"},
        )
        assert paid.status_code == 200
        assert paid.json()["status"] == "PAID"
        assert paid.json()["paid_at"] is not None

        client_login = await http_client.post(
            "/api/v1/auth/token", data={"username": client_email, "password": password}
        )
        client_token = client_login.json()["access_token"]
        listed = await http_client.get(
            "/api/v1/invoices", headers={"Authorization": f"Bearer {client_token}"}
        )
        assert listed.status_code == 200
        assert [item["number"] for item in listed.json()] == ["FAT-001"]
