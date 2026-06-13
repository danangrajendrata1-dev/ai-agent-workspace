"""create tools and agent_tools tables

Revision ID: 20260611_06
Revises: 20260611_05
Create Date: 2026-06-11 22:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260611_06"
down_revision = "20260611_05"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tools",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=150), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tool_type", sa.String(length=50), nullable=False),
        sa.Column("source_type", sa.String(length=30), nullable=True),
        sa.Column("source_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("input_schema", sa.JSON(), nullable=True),
        sa.Column("output_schema", sa.JSON(), nullable=True),
        sa.Column("risk_level", sa.String(length=30), nullable=False),
        sa.Column("approval_required", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("timeout_seconds", sa.Integer(), server_default="60", nullable=False),
        sa.Column("rate_limit_per_hour", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="active", nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_tools_slug"),
    )
    op.create_index("ix_tools_slug", "tools", ["slug"], unique=True)
    op.create_index("ix_tools_tool_type", "tools", ["tool_type"], unique=False)
    op.create_index("ix_tools_source_type", "tools", ["source_type"], unique=False)
    op.create_index("ix_tools_risk_level", "tools", ["risk_level"], unique=False)
    op.create_index("ix_tools_status", "tools", ["status"], unique=False)

    op.create_table(
        "agent_tools",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tool_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("permission_mode", sa.String(length=20), nullable=False),
        sa.Column("override_approval_required", sa.Boolean(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tool_id"], ["tools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_id", "tool_id", name="uq_agent_tools_agent_id_tool_id"),
    )


def downgrade() -> None:
    op.drop_table("agent_tools")
    op.drop_index("ix_tools_status", table_name="tools")
    op.drop_index("ix_tools_risk_level", table_name="tools")
    op.drop_index("ix_tools_source_type", table_name="tools")
    op.drop_index("ix_tools_tool_type", table_name="tools")
    op.drop_index("ix_tools_slug", table_name="tools")
    op.drop_table("tools")
