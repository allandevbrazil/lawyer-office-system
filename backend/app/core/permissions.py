from collections.abc import Callable

from fastapi import HTTPException, status

from app.models import User, UserRole


def require_roles(*allowed_roles: UserRole) -> Callable[[User], User]:
    allowed = set(allowed_roles)

    def dependency(current_user: User) -> User:
        if current_user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return dependency


def ensure_same_firm(current_user: User, firm_id: object) -> None:
    if current_user.firm_id != firm_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")


def can_read_client(current_user: User, client_user_id: object | None) -> bool:
    if current_user.role in {UserRole.MASTER, UserRole.FUNCIONARIO}:
        return True
    return current_user.role == UserRole.CLIENTE and current_user.id == client_user_id
