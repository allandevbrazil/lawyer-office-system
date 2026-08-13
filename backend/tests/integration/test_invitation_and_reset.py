import uuid

import httpx
import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db import async_session_factory, engine
from app.main import app
from app.models import Firm, User, UserRole, UserStatus
from app.schemas.auth import ClientInvitationCreate
from app.services.invitation_service import InvitationService


@pytest.fixture(autouse=True)
async def dispose_database_engine() -> None:
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_invited_client_can_register_only_once() -> None:
    email = f"client-{uuid.uuid4()}@example.com"
    async with async_session_factory() as session:
        firm = Firm(name="Invitation Test Firm")
        session.add(firm)
        await session.flush()
        inviter = User(
            firm_id=firm.id,
            email=f"staff-{uuid.uuid4()}@example.com",
            password_hash=hash_password("staff-password-123"),
            full_name="Staff",
            role=UserRole.FUNCIONARIO,
            status=UserStatus.ACTIVE,
        )
        session.add(inviter)
        await session.flush()
        invitation, raw_token = await InvitationService(
            session, get_settings()
        ).create_client_invitation(
            ClientInvitationCreate(email=email, full_name="Invited Client"), inviter
        )
        assert invitation.email == email

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        registration = await client.post(
            "/api/v1/auth/register",
            json={
                "invite_token": raw_token,
                "email": email,
                "password": "client-password-123",
                "full_name": "Invited Client",
            },
        )
        assert registration.status_code == 201
        assert registration.json()["role"] == "CLIENTE"

        reused = await client.post(
            "/api/v1/auth/register",
            json={
                "invite_token": raw_token,
                "email": email,
                "password": "client-password-123",
                "full_name": "Invited Client",
            },
        )
        assert reused.status_code == 400


@pytest.mark.asyncio
async def test_forgot_password_is_neutral_for_unknown_email() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "unknown@example.com"},
        )

    assert response.status_code == 202
    assert response.content == b""

    async with async_session_factory() as session:
        assert await session.scalar(select(User).where(User.email == "unknown@example.com")) is None
