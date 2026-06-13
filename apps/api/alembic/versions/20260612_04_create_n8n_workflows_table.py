"""create n8n_workflows table

Revision ID: 20260612_04
Revises: 20260612_03
Create Date: 2026-06-12 02:00:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20260612_04"
down_revision = "20260612_03"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "n8n_workflows",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("slug", sa.String(length=180), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("workflow_external_id", sa.String(length=180), nullable=True),
        sa.Column("trigger_type", sa.String(length=50), nullable=False),
        sa.Column("webhook_url_reference", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=30), server_default="inactive", nullable=False),
        sa.Column("risk_level", sa.String(length=30), nullable=False),
        sa.Column("approval_required", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug", name="uq_n8n_workflows_slug"),
    )
    op.create_index("ix_n8n_workflows_owner_id", "n8n_workflows", ["owner_id"], unique=False)
    op.create_index("ix_n8n_workflows_slug", "n8n_workflows", ["slug"], unique=False)
    op.create_index("ix_n8n_workflows_status", "n8n_workflows", ["status"], unique=False)
    op.create_index("ix_n8n_workflows_risk_level", "n8n_workflows", ["risk_level"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_n8n_workflows_risk_level", table_name="n8n_workflows")
    op.drop_index("ix_n8n_workflows_status", table_name="n8n_workflows")
    op.drop_index("ix_n8n_workflows_slug", table_name="n8n_workflows")
    op.drop_index("ix_n8n_workflows_owner_id", table_name="n8n_workflows")
    op.drop_table("n8n_workflows")
