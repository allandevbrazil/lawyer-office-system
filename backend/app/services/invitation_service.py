from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.core.security import create_refresh_token, hash_password, hash_token
from app.models import Client, ClientInvitation, User, UserRole, UserStatus
from app.schemas.auth import ClientInvitationCreate, ClientRegistration
from app.services.email_service import EmailService


class InvitationService:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self.session = session
        self.settings = settings
        self.email_service = EmailService(settings)

    async def create_client_invitation(
        self, payload: ClientInvitationCreate, invited_by: User
    ) -> tuple[ClientInvitation, str]:
        raw_token = create_refresh_token()
        invitation = ClientInvitation(
            firm_id=invited_by.firm_id,
            invited_by=invited_by.id,
            email=str(payload.email).lower(),
            full_name=payload.full_name,
            token_hash=hash_token(raw_token),
            expires_at=datetime.now(UTC) + timedelta(days=3),
        )
        self.session.add(invitation)
        await self.session.commit()
        await self.email_service.send(
            recipient=invitation.email,
            subject="Convite para acessar o LawFirm ERP",
            body=f"Conclua seu cadastro usando este convite: {self.settings.frontend_base_url}/cadastro?invite={raw_token}",
            html=self._invitation_email(invitation.full_name, raw_token),
        )
        return invitation, raw_token

    def _invitation_email(self, full_name: str, raw_token: str) -> str:
        link = f"{self.settings.frontend_base_url}/cadastro?invite={raw_token}"
        return f"""<!doctype html><html lang=\"pt-BR\"><body style=\"margin:0;background:#fcf9f2;color:#1c1c18;font-family:Arial,sans-serif;padding:24px\"><div style=\"max-width:620px;margin:auto;background:#fff;border:1px solid #c4c6cb;border-radius:8px;overflow:hidden\"><header style=\"padding:36px;text-align:center;border-bottom:1px solid #e5e2db\"><div style=\"width:56px;height:56px;line-height:56px;margin:auto;border-radius:50%;background:#121c26;color:#fff;font-size:26px\">⚖</div><h1 style=\"font-family:Georgia,serif;margin:16px 0 4px\">Lex Modern</h1><p style=\"color:#44474b;text-transform:uppercase;letter-spacing:2px;font-size:11px\">Legal Management Systems</p></header><main style=\"padding:40px;text-align:center\"><h2 style=\"font-family:Georgia,serif;font-size:26px\">Convite exclusivo</h2><p style=\"color:#44474b;line-height:1.7\">Olá, {full_name}.<br><br>Você foi convidado a se juntar à equipe da Lex Modern. Crie sua conta para acessar o portal de gestão jurídica.</p><a href=\"{link}\" style=\"display:inline-block;margin:18px 0;padding:14px 28px;background:#7b5647;color:#fff;text-decoration:none;border-radius:4px;font-weight:bold\">Aceitar convite e criar conta</a><p style=\"color:#75777c;font-size:12px\">Este link expira em 3 dias.</p></main><footer style=\"padding:24px;text-align:center;background:#f6f3ec;color:#44474b;font-size:12px\">Lex Modern · Gestão jurídica elevada</footer></div></body></html>"""

    async def accept_client_invitation(self, payload: ClientRegistration) -> User:
        invitation = await self.session.scalar(
            select(ClientInvitation).where(
                ClientInvitation.token_hash == hash_token(payload.invite_token)
            )
        )
        now = datetime.now(UTC)
        if not invitation or invitation.accepted_at or invitation.expires_at <= now:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid invitation"
            )
        if str(payload.email).lower() != invitation.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email does not match invitation"
            )
        existing = await self.session.scalar(select(User).where(User.email == invitation.email))
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
            )
        user = User(
            firm_id=invitation.firm_id,
            email=invitation.email,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name or invitation.full_name,
            phone=payload.phone,
            role=UserRole.CLIENTE,
            status=UserStatus.ACTIVE,
        )
        self.session.add(user)
        await self.session.flush()
        self.session.add(
            Client(
                firm_id=invitation.firm_id,
                user_id=user.id,
                type="PF",
                name=user.full_name,
                email=user.email,
                phone=user.phone,
            )
        )
        invitation.accepted_at = now
        await self.session.commit()
        return user
