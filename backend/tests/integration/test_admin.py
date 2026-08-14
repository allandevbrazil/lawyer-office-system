import uuid

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
async def test_admin_roles_and_wiki_visibility() -> None:
    master_email = f"admin-master-{uuid.uuid4()}@example.com"
    client_email = f"admin-client-{uuid.uuid4()}@example.com"
    password = "admin-test-password-123"

    async with async_session_factory() as session:
        firm = Firm(name="Admin Test Firm")
        session.add(firm)
        await session.flush()
        master = User(
            firm_id=firm.id,
            email=master_email,
            password_hash=hash_password(password),
            full_name="Admin Master",
            role=UserRole.MASTER,
            status=UserStatus.ACTIVE,
        )
        client_user = User(
            firm_id=firm.id,
            email=client_email,
            password_hash=hash_password(password),
            full_name="Admin Client",
            role=UserRole.CLIENTE,
            status=UserStatus.ACTIVE,
        )
        session.add_all([master, client_user])
        await session.flush()
        session.add(
            Client(
                firm_id=firm.id,
                user_id=client_user.id,
                type="PF",
                name="Admin Client",
                email=client_email,
            )
        )
        await session.commit()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        master_login = await client.post(
            "/api/v1/auth/token", data={"username": master_email, "password": password}
        )
        master_token = master_login.json()["access_token"]
        created = await client.post(
            "/api/v1/wiki/articles",
            headers={"Authorization": f"Bearer {master_token}"},
            json={
                "title": "Manual",
                "slug": f"manual-{uuid.uuid4()}",
                "content_markdown": "# Manual",
                "status": "PUBLISHED",
            },
        )
        assert created.status_code == 201
        settings = await client.get(
            "/api/v1/settings/firm", headers={"Authorization": f"Bearer {master_token}"}
        )
        assert settings.status_code == 404

        client_login = await client.post(
            "/api/v1/auth/token", data={"username": client_email, "password": password}
        )
        client_token = client_login.json()["access_token"]
        forbidden = await client.get(
            "/api/v1/settings/firm", headers={"Authorization": f"Bearer {client_token}"}
        )
        assert forbidden.status_code == 403
        wiki = await client.get(
            "/api/v1/wiki/articles", headers={"Authorization": f"Bearer {client_token}"}
        )
        assert wiki.status_code == 403
        staff = await client.get(
            "/api/v1/staff", headers={"Authorization": f"Bearer {client_token}"}
        )
        assert staff.status_code == 403

        staff_created = await client.post(
            "/api/v1/staff",
            headers={"Authorization": f"Bearer {master_token}"},
            json={
                "email": f"employee-{uuid.uuid4()}@example.com",
                "full_name": "Admin Employee",
                "password": password,
            },
        )
        assert staff_created.status_code == 201
        role_escalation = await client.patch(
            f"/api/v1/staff/{staff_created.json()['id']}",
            headers={"Authorization": f"Bearer {master_token}"},
            json={"role": "MASTER"},
        )
        assert role_escalation.status_code == 422
