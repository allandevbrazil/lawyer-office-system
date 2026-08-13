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
async def test_document_upload_download_and_visibility() -> None:
    staff_email = f"documents-staff-{uuid.uuid4()}@example.com"
    client_email = f"documents-client-{uuid.uuid4()}@example.com"
    password = "documents-test-password-123"

    async with async_session_factory() as session:
        firm = Firm(name="Documents Test Firm")
        session.add(firm)
        await session.flush()
        staff = User(
            firm_id=firm.id,
            email=staff_email,
            password_hash=hash_password(password),
            full_name="Documents Staff",
            role=UserRole.FUNCIONARIO,
            status=UserStatus.ACTIVE,
        )
        client_user = User(
            firm_id=firm.id,
            email=client_email,
            password_hash=hash_password(password),
            full_name="Documents Client",
            role=UserRole.CLIENTE,
            status=UserStatus.ACTIVE,
        )
        session.add_all([staff, client_user])
        await session.flush()
        client = Client(
            firm_id=firm.id,
            user_id=client_user.id,
            type="PF",
            name="Documents Client",
            email=client_email,
        )
        session.add(client)
        await session.commit()
        client_id = client.id

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        login = await client.post(
            "/api/v1/auth/token", data={"username": staff_email, "password": password}
        )
        staff_token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {staff_token}"}
        internal = await client.post(
            "/api/v1/documents",
            headers=headers,
            data={"client_id": str(client_id), "visibility": "INTERNAL"},
            files={"file": ("internal.txt", b"internal", "text/plain")},
        )
        shared = await client.post(
            "/api/v1/documents",
            headers=headers,
            data={"client_id": str(client_id), "visibility": "CLIENT"},
            files={"file": ("shared.txt", b"shared", "text/plain")},
        )
        assert internal.status_code == 201
        assert shared.status_code == 201
        shared_id = shared.json()["id"]

        client_login = await client.post(
            "/api/v1/auth/token", data={"username": client_email, "password": password}
        )
        client_token = client_login.json()["access_token"]
        listed = await client.get(
            "/api/v1/documents", headers={"Authorization": f"Bearer {client_token}"}
        )
        assert listed.status_code == 200
        assert [document["file_name"] for document in listed.json()] == ["shared.txt"]

        download = await client.get(
            f"/api/v1/documents/{shared_id}/download",
            headers={"Authorization": f"Bearer {client_token}"},
        )
        assert download.status_code == 200
        assert download.content == b"shared"
