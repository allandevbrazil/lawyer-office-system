from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.core.config import Settings, get_settings
from app.core.rate_limit import enforce_rate_limit
from app.db import get_db_session
from app.models import User, UserRole
from app.schemas.auth import (
    ClientInvitationCreate,
    ClientInvitationResponse,
    ClientRegistration,
    PasswordResetConfirm,
    PasswordResetRequest,
    TokenResponse,
    UserResponse,
)
from app.services.auth_service import AuthService
from app.services.invitation_service import InvitationService

router = APIRouter(prefix="/auth", tags=["authentication"])
client_router = APIRouter(prefix="/client-invitations", tags=["clients"])


async def get_auth_service(
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> AuthService:
    return AuthService(session, settings)


AuthServiceDependency = Annotated[AuthService, Depends(get_auth_service)]


def set_refresh_cookie(response: Response, token: str, settings: Settings) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="none" if settings.app_env == "production" else "lax",
        max_age=settings.refresh_token_expire_days * 86400,
        path="/api/v1/auth",
    )


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Authenticate a user",
    description=(
        "Authenticates with OAuth2 form fields and sets a rotating HttpOnly refresh cookie."
    ),
    responses={401: {"description": "Invalid credentials"}},
)
async def login(
    request: Request,
    response: Response,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: AuthServiceDependency,
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    enforce_rate_limit(request, bucket="auth-token", limit=20, window_seconds=60)
    user = await auth_service.authenticate(form.username, form.password)
    token_response, refresh_token = await auth_service.issue_tokens(user)
    set_refresh_cookie(response, refresh_token, settings)
    return token_response


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rotate the refresh token",
    responses={401: {"description": "Invalid, expired, or reused refresh token"}},
)
async def refresh(
    request: Request,
    response: Response,
    auth_service: AuthServiceDependency,
    settings: Settings = Depends(get_settings),
) -> TokenResponse:
    enforce_rate_limit(request, bucket="auth-refresh", limit=60, window_seconds=60)
    refresh_token = request.cookies.get(settings.refresh_cookie_name)
    token_response, new_refresh_token = await auth_service.rotate_refresh_token(refresh_token or "")
    set_refresh_cookie(response, new_refresh_token, settings)
    return token_response


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT, summary="Revoke the refresh token")
async def logout(
    request: Request,
    response: Response,
    auth_service: AuthServiceDependency,
    settings: Settings = Depends(get_settings),
) -> None:
    await auth_service.revoke_refresh_token(request.cookies.get(settings.refresh_cookie_name))
    response.delete_cookie(settings.refresh_cookie_name, path="/api/v1/auth")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get the authenticated user",
    responses={401: {"description": "Missing or invalid access token"}},
)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Complete an invited client registration",
)
async def register_client(
    request: Request,
    payload: ClientRegistration,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> UserResponse:
    enforce_rate_limit(request, bucket="auth-register", limit=10, window_seconds=60)
    user = await InvitationService(session, settings).accept_client_invitation(payload)
    return UserResponse.model_validate(user)


@router.post(
    "/forgot-password",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Request a password reset",
    description="Always returns 202 and never reveals whether an email is registered.",
)
async def forgot_password(
    request: Request,
    payload: PasswordResetRequest,
    auth_service: AuthServiceDependency,
) -> Response:
    enforce_rate_limit(request, bucket="auth-forgot-password", limit=5, window_seconds=60)
    await auth_service.request_password_reset(str(payload.email))
    return Response(status_code=status.HTTP_202_ACCEPTED)


@router.post("/reset-password", status_code=status.HTTP_204_NO_CONTENT, summary="Reset a password")
async def reset_password(
    request: Request,
    payload: PasswordResetConfirm,
    auth_service: AuthServiceDependency,
) -> Response:
    enforce_rate_limit(request, bucket="auth-reset-password", limit=10, window_seconds=60)
    await auth_service.reset_password(payload.token, payload.new_password)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@client_router.post(
    "",
    response_model=ClientInvitationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Invite a client",
)
async def create_client_invitation(
    request: Request,
    payload: ClientInvitationCreate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> ClientInvitationResponse:
    enforce_rate_limit(request, bucket="client-invitation", limit=10, window_seconds=60)
    if current_user.role not in {UserRole.MASTER, UserRole.FUNCIONARIO}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Staff role required")
    invitation, _ = await InvitationService(session, settings).create_client_invitation(
        payload, current_user
    )
    return ClientInvitationResponse.model_validate(invitation)
