"""create workflow foundation tables

Revision ID: 20260617_02
Revises: 20260617_01
Create Date: 2026-06-17 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260617_02"
down_revision = "20260617_01"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workflow_consents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("template_id", sa.String(length=100), nullable=False),
        sa.Column("template_version", sa.String(length=50), nullable=False),
        sa.Column(
            "consented_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint("user_id", "template_id", "template_version", name="uq_workflow_consents_user_template_version"),
    )
    op.create_index("ix_workflow_consents_user_id", "workflow_consents", ["user_id"], unique=False)
    op.create_index(
        "ix_workflow_consents_user_id_template_id",
        "workflow_consents",
        ["user_id", "template_id"],
        unique=False,
    )

    op.create_table(
        "workflow_executions",
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
            sa.ForeignKey("agents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "skill_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("skills.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("template_id", sa.String(length=100), nullable=False),
        sa.Column("template_version", sa.String(length=50), nullable=False),
        sa.Column(
            "consent_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("workflow_consents.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("webhook_url", sa.String(length=500), nullable=True),
        sa.Column("input_payload_sanitized", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("http_status_code", sa.Integer(), nullable=True),
        sa.Column(
            "executed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    op.create_index("ix_workflow_executions_user_id", "workflow_executions", ["user_id"], unique=False)
    op.create_index(
        "ix_workflow_executions_user_id_executed_at",
        "workflow_executions",
        ["user_id", "executed_at"],
        unique=False,
    )
    op.create_index("ix_workflow_executions_template_id", "workflow_executions", ["template_id"], unique=False)
    op.create_index("ix_workflow_executions_agent_id", "workflow_executions", ["agent_id"], unique=False)
    op.create_index("ix_workflow_executions_skill_id", "workflow_executions", ["skill_id"], unique=False)

    op.create_table(
        "workflow_skill_template_bindings",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "skill_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("skills.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("template_id", sa.String(length=100), nullable=False),
        sa.Column("template_version", sa.String(length=50), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.UniqueConstraint(
            "user_id",
            "skill_id",
            "template_id",
            "template_version",
            name="uq_workflow_skill_template_bindings_user_skill_template_version",
        ),
    )
    op.create_index(
        "ix_workflow_skill_template_bindings_user_id",
        "workflow_skill_template_bindings",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_workflow_skill_template_bindings_skill_id",
        "workflow_skill_template_bindings",
        ["skill_id"],
        unique=False,
    )
    op.create_index(
        "ix_workflow_skill_template_bindings_user_id_template_id",
        "workflow_skill_template_bindings",
        ["user_id", "template_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_workflow_skill_template_bindings_user_id_template_id",
        table_name="workflow_skill_template_bindings",
    )
    op.drop_index("ix_workflow_skill_template_bindings_skill_id", table_name="workflow_skill_template_bindings")
    op.drop_index("ix_workflow_skill_template_bindings_user_id", table_name="workflow_skill_template_bindings")
    op.drop_table("workflow_skill_template_bindings")

    op.drop_index("ix_workflow_executions_skill_id", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_agent_id", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_template_id", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_user_id_executed_at", table_name="workflow_executions")
    op.drop_index("ix_workflow_executions_user_id", table_name="workflow_executions")
    op.drop_table("workflow_executions")

    op.drop_index("ix_workflow_consents_user_id_template_id", table_name="workflow_consents")
    op.drop_index("ix_workflow_consents_user_id", table_name="workflow_consents")
    op.drop_table("workflow_consents")
