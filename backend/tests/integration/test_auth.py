import uuid

import httpx
import pytest
from sqlalchemy import select

from app.core.security import hash_password
from app.db import async_session_factory, engine
from app.main import app
from app.models import Firm, User, UserRole, UserStatus


@pytest.fixture(autouse=True)
async def dispose_database_engine() -> None:
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_authentication_lifecycle() -> None:
    email = f"master-{uuid.uuid4()}@example.com"
    password = "portfolio-master-password-123"

    async with async_session_factory() as session:
        firm = Firm(name="Integration Test Firm")
        session.add(firm)
        await session.flush()
        session.add(
            User(
                firm_id=firm.id,
                email=email,
                password_hash=hash_password(password),
                full_name="Integration Master",
                role=UserRole.MASTER,
                status=UserStatus.ACTIVE,
            )
        )
        await session.commit()

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        login = await client.post(
            "/api/v1/auth/token",
            data={"username": email, "password": password},
        )
        assert login.status_code == 200
        access_token = login.json()["access_token"]
        old_refresh = client.cookies.get("lawfirm_refresh")

        me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert me.status_code == 200
        assert me.json()["email"] == email
        assert me.json()["role"] == "MASTER"

        refresh = await client.post("/api/v1/auth/refresh")
        assert refresh.status_code == 200
        assert client.cookies.get("lawfirm_refresh") != old_refresh

        logout = await client.post("/api/v1/auth/logout")
        assert logout.status_code == 204

        client.cookies.set("lawfirm_refresh", old_refresh)
        reused_refresh = await client.post("/api/v1/auth/refresh")
        assert reused_refresh.status_code == 401


@pytest.mark.asyncio
async def test_invalid_credentials_are_rejected() -> None:
    async with async_session_factory() as session:
        user = await session.scalar(select(User).where(User.role == UserRole.MASTER))

    assert user is not None
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
        response = await client.post(
            "/api/v1/auth/token",
            data={"username": user.email, "password": "wrong-password"},
        )

    assert response.status_code == 401
