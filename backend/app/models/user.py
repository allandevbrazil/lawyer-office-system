import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class UserRole(enum.StrEnum):
    MASTER = "MASTER"
    FUNCIONARIO = "FUNCIONARIO"
    CLIENTE = "CLIENTE"


class UserStatus(enum.StrEnum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    INVITED = "INVITED"


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[UUIDPrimaryKey]
    firm_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("firms.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    full_name: Mapped[str] = mapped_column(String(160), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, validate_strings=True), nullable=False
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, native_enum=False, validate_strings=True), nullable=False
    )
    phone: Mapped[str | None] = mapped_column(String(32))
