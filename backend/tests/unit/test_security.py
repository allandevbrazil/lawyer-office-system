from uuid import uuid4

import jwt
import pytest

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    hash_password,
    hash_token,
    verify_password,
)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        jwt_secret_key="test-secret-key-with-at-least-32-bytes", access_token_expire_minutes=5
    )


def test_password_hash_is_verifiable_and_not_plaintext() -> None:
    password = "a-strong-password-123"
    hashed = hash_password(password)

    assert hashed != password
    assert verify_password(password, hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_contains_required_claims(settings: Settings) -> None:
    user_id = uuid4()
    firm_id = uuid4()
    token = create_access_token(user_id=user_id, firm_id=firm_id, role="MASTER", settings=settings)

    payload = decode_access_token(token, settings)

    assert payload["sub"] == str(user_id)
    assert payload["firm_id"] == str(firm_id)
    assert payload["role"] == "MASTER"
    assert payload["type"] == "access"


def test_access_token_rejects_wrong_secret(settings: Settings) -> None:
    token = create_access_token(user_id=uuid4(), firm_id=uuid4(), role="CLIENTE", settings=settings)

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(token, Settings(jwt_secret_key="another-secret-with-at-least-32-bytes"))


def test_refresh_tokens_are_random_and_hashable() -> None:
    first = create_refresh_token()
    second = create_refresh_token()

    assert first != second
    assert hash_token(first) != hash_token(second)
