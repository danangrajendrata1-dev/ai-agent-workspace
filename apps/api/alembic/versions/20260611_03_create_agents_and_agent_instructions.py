"""create agents and agent_instructions tables

Revision ID: 20260611_03
Revises: 20260611_02
Create Date: 2026-06-11 21:10:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260611_03"
down_revision = "20260611_02"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("role_description", sa.Text(), nullable=False),
        sa.Column("default_model_provider_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("default_model_name", sa.String(length=120), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="active", nullable=False),
        sa.Column("max_steps", sa.Integer(), server_default="10", nullable=False),
        sa.Column("max_runtime_seconds", sa.Integer(), server_default="300", nullable=False),
        sa.Column("max_token_budget", sa.Integer(), nullable=True),
        sa.Column(
            "requires_approval_by_default",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
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
        sa.ForeignKeyConstraint(["default_model_provider_id"], ["model_providers.id"]),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_agents_slug"),
    )
    op.create_index("ix_agents_owner_id", "agents", ["owner_id"], unique=False)
    op.create_index("ix_agents_slug", "agents", ["slug"], unique=True)
    op.create_index("ix_agents_status", "agents", ["status"], unique=False)

    op.create_table(
        "agent_instructions",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("agent_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("instruction_text", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
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
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_agent_instructions_agent_id", "agent_instructions", ["agent_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_agent_instructions_agent_id", table_name="agent_instructions")
    op.drop_table("agent_instructions")
    op.drop_index("ix_agents_status", table_name="agents")
    op.drop_index("ix_agents_slug", table_name="agents")
    op.drop_index("ix_agents_owner_id", table_name="agents")
    op.drop_table("agents")
