import enum
import uuid

from sqlalchemy import JSON, Enum, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class ClientType(enum.StrEnum):
    PF = "PF"
    PJ = "PJ"


class ClientStatus(enum.StrEnum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class Client(TimestampMixin, Base):
    __tablename__ = "clients"

    id: Mapped[UUIDPrimaryKey]
    firm_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("firms.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), unique=True
    )
    type: Mapped[ClientType] = mapped_column(
        Enum(ClientType, native_enum=False, validate_strings=True), nullable=False
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(128))
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(32))
    address_json: Mapped[dict | None] = mapped_column(JSON)
    notes: Mapped[str | None] = mapped_column(String(4000))
    status: Mapped[ClientStatus] = mapped_column(
        Enum(ClientStatus, native_enum=False, validate_strings=True),
        default=ClientStatus.ACTIVE,
        nullable=False,
    )
