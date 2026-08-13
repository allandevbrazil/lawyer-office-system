"""create cases and case events

Revision ID: 0003_cases
Revises: 0002_client_invitations
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_cases"
down_revision: Union[str, None] = "0002_client_invitations"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cases",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("firm_id", sa.Uuid(), nullable=False),
        sa.Column("client_id", sa.Uuid(), nullable=False),
        sa.Column("responsible_user_id", sa.Uuid()),
        sa.Column("case_number", sa.String(length=64)),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("court", sa.String(length=200)),
        sa.Column("jurisdiction", sa.String(length=160)),
        sa.Column("case_type", sa.String(length=120)),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("priority", sa.String(length=16), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("closed_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["firm_id"], ["firms.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["responsible_user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("status IN ('ACTIVE', 'SUSPENDED', 'ARCHIVED')", name="ck_cases_status"),
    )
    op.create_index("ix_cases_firm_id", "cases", ["firm_id"])
    op.create_index("ix_cases_client_id", "cases", ["client_id"])
    op.create_index("ix_cases_responsible_user_id", "cases", ["responsible_user_id"])
    op.create_index("ix_cases_case_number", "cases", ["case_number"])

    op.create_table(
        "case_parties",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("role", sa.String(length=80), nullable=False),
        sa.Column("document_number", sa.String(length=128)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_case_parties_case_id", "case_parties", ["case_id"])

    op.create_table(
        "case_events",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("case_id", sa.Uuid(), nullable=False),
        sa.Column("author_user_id", sa.Uuid(), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("visibility", sa.String(length=16), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["cases.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("visibility IN ('INTERNAL', 'CLIENT')", name="ck_case_events_visibility"),
    )
    op.create_index("ix_case_events_case_id", "case_events", ["case_id"])


def downgrade() -> None:
    op.drop_index("ix_case_events_case_id", table_name="case_events")
    op.drop_table("case_events")
    op.drop_index("ix_case_parties_case_id", table_name="case_parties")
    op.drop_table("case_parties")
    op.drop_index("ix_cases_case_number", table_name="cases")
    op.drop_index("ix_cases_responsible_user_id", table_name="cases")
    op.drop_index("ix_cases_client_id", table_name="cases")
    op.drop_index("ix_cases_firm_id", table_name="cases")
    op.drop_table("cases")
