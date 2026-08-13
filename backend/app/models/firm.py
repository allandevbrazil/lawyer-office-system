import uuid

from sqlalchemy import JSON, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDPrimaryKey


class Firm(TimestampMixin, Base):
    __tablename__ = "firms"

    id: Mapped[UUIDPrimaryKey]
    name: Mapped[str] = mapped_column(String(160), nullable=False)

    config: Mapped["FirmConfig"] = relationship(back_populates="firm", uselist=False)


class FirmConfig(TimestampMixin, Base):
    __tablename__ = "firm_configs"

    id: Mapped[UUIDPrimaryKey]
    firm_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("firms.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
        index=True,
    )
    legal_name: Mapped[str | None] = mapped_column(String(200))
    trade_name: Mapped[str | None] = mapped_column(String(160))
    tax_id: Mapped[str | None] = mapped_column(String(32))
    email: Mapped[str | None] = mapped_column(String(320))
    phone: Mapped[str | None] = mapped_column(String(32))
    address_json: Mapped[dict | None] = mapped_column(JSON)
    logo_url: Mapped[str | None] = mapped_column(String(500))
    timezone: Mapped[str] = mapped_column(String(64), default="America/Sao_Paulo", nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="BRL", nullable=False)
    settings_json: Mapped[dict | None] = mapped_column(JSON)

    firm: Mapped[Firm] = relationship(back_populates="config")
