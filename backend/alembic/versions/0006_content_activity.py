"""create wiki and activities

Revision ID: 0006_content_activity
Revises: 0005_documents
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_content_activity"
down_revision: Union[str, None] = "0005_documents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "wiki_articles",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("firm_id", sa.Uuid(), nullable=False),
        sa.Column("author_user_id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=240), nullable=False),
        sa.Column("slug", sa.String(length=260), nullable=False),
        sa.Column("content_markdown", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=120)),
        sa.Column("status", sa.String(length=16), nullable=False),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["firm_id"], ["firms.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["author_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("firm_id", "slug", name="uq_wiki_firm_slug"),
        sa.CheckConstraint(
            "status IN ('DRAFT', 'PUBLISHED', 'ARCHIVED')", name="ck_wiki_status"
        ),
    )
    op.create_index("ix_wiki_articles_firm_id", "wiki_articles", ["firm_id"])
    op.create_index("ix_wiki_articles_slug", "wiki_articles", ["slug"])
    op.create_table(
        "activities",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("firm_id", sa.Uuid(), nullable=False),
        sa.Column("actor_user_id", sa.Uuid(), nullable=False),
        sa.Column("entity_type", sa.String(length=80), nullable=False),
        sa.Column("entity_id", sa.Uuid()),
        sa.Column("action", sa.String(length=80), nullable=False),
        sa.Column("description", sa.String(length=500)),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["firm_id"], ["firms.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["actor_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activities_firm_id", "activities", ["firm_id"])


def downgrade() -> None:
    op.drop_index("ix_activities_firm_id", table_name="activities")
    op.drop_table("activities")
    op.drop_index("ix_wiki_articles_slug", table_name="wiki_articles")
    op.drop_index("ix_wiki_articles_firm_id", table_name="wiki_articles")
    op.drop_table("wiki_articles")
