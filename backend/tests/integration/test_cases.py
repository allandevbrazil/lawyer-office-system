import uuid
from datetime import UTC, datetime

import httpx
import pytest

from app.core.security import hash_password
from app.db import async_session_factory, engine
from app.main import app
from app.models import Case, Client, Firm, User, UserRole, UserStatus


@pytest.fixture(autouse=True)
async def dispose_database_engine() -> None:
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_case_isolation_between_clients() -> None:
    staff_email = f"staff-{uuid.uuid4()}@example.com"
    first_email = f"first-{uuid.uuid4()}@example.com"
    second_email = f"second-{uuid.uuid4()}@example.com"
    password = "case-test-password-123"

    async with async_session_factory() as session:
        firm = Firm(name="Cases Test Firm")
        session.add(firm)
        await session.flush()
        staff = User(
            firm_id=firm.id,
            email=staff_email,
            password_hash=hash_password(password),
            full_name="Staff",
            role=UserRole.MASTER,
            status=UserStatus.ACTIVE,
        )
        first_user = User(
            firm_id=firm.id,
            email=first_email,
            password_hash=hash_password(password),
            full_name="First Client",
            role=UserRole.CLIENTE,
            status=UserStatus.ACTIVE,
        )
        second_user = User(
            firm_id=firm.id,
            email=second_email,
            password_hash=hash_password(password),
            full_name="Second Client",
            role=UserRole.CLIENTE,
            status=UserStatus.ACTIVE,
        )
        session.add_all([staff, first_user, second_user])
        await session.flush()
        first_client = Client(
            firm_id=firm.id,
            user_id=first_user.id,
            type="PF",
            name="First Client",
            email=first_email,
        )
        second_client = Client(
            firm_id=firm.id,
            user_id=second_user.id,
            type="PF",
            name="Second Client",
            email=second_email,
        )
        session.add_all([first_client, second_client])
        await session.flush()
        other_case = Case(
            firm_id=firm.id,
            client_id=second_client.id,
            title="Other client case",
            status="ACTIVE",
            priority="NORMAL",
            opened_at=datetime.now(UTC),
        )
        session.add(other_case)
        await session.commit()
        other_case_id = other_case.id
        first_client_id = first_client.id

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        staff_login = await client.post(
            "/api/v1/auth/token", data={"username": staff_email, "password": password}
        )
        staff_token = staff_login.json()["access_token"]
        all_clients = await client.get(
            "/api/v1/clients", headers={"Authorization": f"Bearer {staff_token}"}
        )
        assert all_clients.status_code == 200
        assert {item["name"] for item in all_clients.json()} == {"First Client", "Second Client"}
        blocked_client_delete = await client.delete(
            f"/api/v1/clients/{second_client.id}",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert blocked_client_delete.status_code == 409
        created = await client.post(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {staff_token}"},
            json={"client_id": str(first_client_id), "title": "First client case"},
        )
        assert created.status_code == 201
        invalid = await client.post(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {staff_token}"},
            json={"client_id": str(first_client_id), "title": "x"},
        )
        assert invalid.status_code == 422

        first_login = await client.post(
            "/api/v1/auth/token", data={"username": first_email, "password": password}
        )
        first_token = first_login.json()["access_token"]
        listed = await client.get(
            "/api/v1/cases", headers={"Authorization": f"Bearer {first_token}"}
        )
        assert listed.status_code == 200
        assert {item["title"] for item in listed.json()} == {"First client case"}

        hidden = await client.get(
            f"/api/v1/cases/{other_case_id}",
            headers={"Authorization": f"Bearer {first_token}"},
        )
        assert hidden.status_code == 404

        forbidden = await client.post(
            "/api/v1/cases",
            headers={"Authorization": f"Bearer {first_token}"},
            json={"client_id": str(first_client_id), "title": "Forbidden case"},
        )
        assert forbidden.status_code == 403

        deleted = await client.delete(
            f"/api/v1/cases/{created.json()['id']}",
            headers={"Authorization": f"Bearer {staff_token}"},
        )
        assert deleted.status_code == 204
        remaining = await client.get(
            "/api/v1/cases", headers={"Authorization": f"Bearer {staff_token}"}
        )
        assert {item["title"] for item in remaining.json()} == {"Other client case"}
