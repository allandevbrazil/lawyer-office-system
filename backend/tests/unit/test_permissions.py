from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from app.core.permissions import can_read_client, ensure_same_firm, require_roles
from app.models import UserRole


def user(role: UserRole, firm_id=None, user_id=None):
    return SimpleNamespace(role=role, firm_id=firm_id or uuid4(), id=user_id or uuid4())


def test_staff_can_read_any_client_and_client_only_self() -> None:
    client = user(UserRole.CLIENTE)
    other_client = uuid4()

    assert can_read_client(user(UserRole.MASTER), other_client)
    assert can_read_client(user(UserRole.FUNCIONARIO), other_client)
    assert can_read_client(client, client.id)
    assert not can_read_client(client, other_client)


def test_same_firm_policy_returns_not_found_for_other_firm() -> None:
    current = user(UserRole.MASTER)
    ensure_same_firm(current, current.firm_id)

    with pytest.raises(HTTPException) as error:
        ensure_same_firm(current, uuid4())

    assert error.value.status_code == 404


def test_role_policy_rejects_unauthorized_role() -> None:
    dependency = require_roles(UserRole.MASTER)

    with pytest.raises(HTTPException) as error:
        dependency(user(UserRole.CLIENTE))

    assert error.value.status_code == 403