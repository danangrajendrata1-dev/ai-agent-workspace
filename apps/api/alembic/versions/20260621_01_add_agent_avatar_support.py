"""add agent avatar support

Revision ID: 20260621_01
Revises: 20260618_01
Create Date: 2026-06-21 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260621_01"
down_revision = "20260618_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("agents", sa.Column("avatar_type", sa.String(length=40), nullable=True))
    op.add_column("agents", sa.Column("avatar_value", sa.Text(), nullable=True))

    op.create_table(
        "agent_avatar_assets",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "agent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("agents.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("storage_backend", sa.String(length=20), nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("safe_filename", sa.String(length=255), nullable=True),
        sa.Column("content_type", sa.String(length=120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("agent_id", name="uq_agent_avatar_assets_agent_id"),
    )
    op.create_index("ix_agent_avatar_assets_user_id", "agent_avatar_assets", ["user_id"], unique=False)
    op.create_index("ix_agent_avatar_assets_agent_id", "agent_avatar_assets", ["agent_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_agent_avatar_assets_agent_id", table_name="agent_avatar_assets")
    op.drop_index("ix_agent_avatar_assets_user_id", table_name="agent_avatar_assets")
    op.drop_table("agent_avatar_assets")
    op.drop_column("agents", "avatar_value")
    op.drop_column("agents", "avatar_type")
