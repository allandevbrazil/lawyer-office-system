import hashlib
import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

import jwt
from pwdlib import PasswordHash

from app.core.config import Settings, get_settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_access_token(
    *, user_id: UUID, firm_id: UUID, role: str, settings: Settings | None = None
) -> str:
    current_settings = settings or get_settings()
    expires_at = datetime.now(UTC) + timedelta(minutes=current_settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "firm_id": str(firm_id),
        "role": role,
        "type": "access",
        "exp": expires_at,
        "iat": datetime.now(UTC),
    }
    return jwt.encode(
        payload, current_settings.jwt_secret_key, algorithm=current_settings.jwt_algorithm
    )


def decode_access_token(token: str, settings: Settings | None = None) -> dict:
    current_settings = settings or get_settings()
    payload = jwt.decode(
        token,
        current_settings.jwt_secret_key,
        algorithms=[current_settings.jwt_algorithm],
        options={"require": ["sub", "firm_id", "role", "type", "exp"]},
    )
    if payload.get("type") != "access":
        raise jwt.InvalidTokenError("Invalid token type")
    return payload


def create_refresh_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
