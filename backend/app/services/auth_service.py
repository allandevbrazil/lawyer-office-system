from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models import RefreshToken, User, UserStatus
from app.schemas.auth import TokenResponse, UserResponse
from app.services.email_service import EmailService


class AuthService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.email_service = EmailService(settings)

    async def authenticate(self, email: str, password: str) -> User:
        user = await self.session.scalar(select(User).where(User.email == email.strip().lower()))
        if (
            not user
            or user.status != UserStatus.ACTIVE
            or not verify_password(password, user.password_hash)
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user

    async def issue_tokens(self, user: User) -> tuple[TokenResponse, str]:
        access_token = create_access_token(
            user_id=user.id,
            firm_id=user.firm_id,
            role=user.role.value,
            settings=self.settings,
        )
        refresh_token = create_refresh_token()
        self.session.add(
            RefreshToken(
                user_id=user.id,
                token_hash=hash_token(refresh_token),
                expires_at=datetime.now(UTC)
                + timedelta(days=self.settings.refresh_token_expire_days),
            )
        )
        await self.session.commit()
        return (
            TokenResponse(
                access_token=access_token,
                expires_in=self.settings.access_token_expire_minutes * 60,
                user=UserResponse.model_validate(user),
            ),
            refresh_token,
        )

    async def rotate_refresh_token(self, refresh_token: str) -> tuple[TokenResponse, str]:
        record = await self.session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token))
        )
        now = datetime.now(UTC)
        if not record or record.revoked_at is not None or record.expires_at <= now:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
            )

        user = await self.session.get(User, record.user_id)
        if not user or user.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive user")

        record.revoked_at = now
        return await self.issue_tokens(user)

    async def revoke_refresh_token(self, refresh_token: str | None) -> None:
        if not refresh_token:
            return
        record = await self.session.scalar(
            select(RefreshToken).where(RefreshToken.token_hash == hash_token(refresh_token))
        )
        if record and record.revoked_at is None:
            record.revoked_at = datetime.now(UTC)
            await self.session.commit()

    async def request_password_reset(self, email: str) -> None:
        from app.core.security import create_refresh_token
        from app.models import PasswordResetToken

        user = await self.session.scalar(select(User).where(User.email == email.strip().lower()))
        if not user:
            return
        raw_token = create_refresh_token()
        self.session.add(
            PasswordResetToken(
                user_id=user.id,
                token_hash=hash_token(raw_token),
                expires_at=datetime.now(UTC) + timedelta(minutes=30),
            )
        )
        await self.session.commit()
        await self.email_service.send(
            recipient=user.email,
            subject="Recuperacao de senha do LawFirm ERP",
            body=f"Use este token para redefinir sua senha: {raw_token}",
        )

    async def reset_password(self, token: str, new_password: str) -> None:
        from app.models import PasswordResetToken

        record = await self.session.scalar(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == hash_token(token))
        )
        now = datetime.now(UTC)
        if not record or record.used_at or record.expires_at <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token"
            )
        user = await self.session.get(User, record.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid reset token"
            )
        user.password_hash = hash_password(new_password)
        record.used_at = now
        await self.session.commit()
